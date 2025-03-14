from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
import json
import typesense
import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional


class Command(BaseCommand):
    help = "Updates Typesense index for specified models"

    def get_client(self) -> typesense.Client:
        """
        Create Typesense client from environment variables
        """
        client = typesense.Client(
            {
                "api_key": os.getenv("TYPESENSE_API_KEY"),
                "nodes": [
                    {
                        "host": os.getenv("TYPESENSE_HOST", "localhost"),
                        "port": os.getenv("TYPESENSE_PORT", "8108"),
                        "protocol": os.getenv("TYPESENSE_PROTOCOL", "http"),
                    }
                ],
                "connection_timeout_seconds": int(os.getenv("TYPESENSE_TIMEOUT", "2")),
            }
        )
        return client

    def create_or_update_collection(
        self, client: typesense.Client, schema: Dict[str, Any]
    ) -> None:
        """
        Create or update a Typesense collection with the given schema
        """
        collection_name = schema["name"]
        try:
            # Try to delete existing collection
            try:
                client.collections[collection_name].delete()
                self.stdout.write(f"Deleted existing collection '{collection_name}'")
            except typesense.exceptions.ObjectNotFound:
                pass

            # Create new collection
            client.collections.create(schema)
            self.stdout.write(f"Created collection '{collection_name}'")
        except typesense.exceptions.TypesenseClientError as e:
            raise CommandError(f"Error creating collection: {str(e)}")

    def import_documents(
        self,
        client: typesense.Client,
        collection_name: str,
        documents: list,
        start_index: int = 0,
    ) -> None:
        """
        Import documents into Typesense collection with batch processing

        Args:
            client: Typesense client
            collection_name: Name of the collection
            documents: List of documents to import
            start_index: Index to start importing from (for resuming)
        """
        try:
            # Configure batch size
            batch_size = int(os.getenv("TYPESENSE_BATCH_SIZE", "500"))

            # Create checkpoint directory if it doesn't exist
            checkpoint_dir = Path(
                os.getenv("TYPESENSE_CHECKPOINT_DIR", "/tmp/typesense_checkpoints")
            )
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_file = (
                checkpoint_dir / f"{collection_name}_upload_checkpoint.pkl"
            )

            # Process in batches
            total_docs = len(documents)
            for i in range(start_index, total_docs, batch_size):
                batch = documents[i : i + batch_size]

                try:
                    results = client.collections[collection_name].documents.import_(
                        batch
                    )

                    # Check for errors in import results
                    errors = [r for r in results if "error" in r]
                    if errors:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Batch {i // batch_size + 1}: {len(errors)} errors in {len(batch)} documents | {errors}"
                            )
                        )

                    # Save checkpoint after successful batch
                    next_index = min(i + batch_size, total_docs)
                    self._save_checkpoint(checkpoint_file, collection_name, next_index)

                    self.stdout.write(f"Imported {next_index}/{total_docs} documents")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error during import at index {i}: {str(e)}")
                    )
                    # Save the current position for resuming
                    self._save_checkpoint(checkpoint_file, collection_name, i)
                    raise

        except Exception as e:
            raise CommandError(f"Error importing documents: {str(e)}")

    def _save_checkpoint(
        self, checkpoint_file: Path, collection_name: str, index: int
    ) -> None:
        """Save checkpoint information for resuming imports"""
        checkpoint_data = {
            "collection_name": collection_name,
            "last_processed_index": index,
            "timestamp": os.path.getmtime(checkpoint_file)
            if checkpoint_file.exists()
            else None,
        }

        with open(checkpoint_file, "wb") as f:
            pickle.dump(checkpoint_data, f)

    def _save_documents_checkpoint(
        self, checkpoint_file: Path, collection_name: str, index: int, documents: list
    ) -> None:
        """Save checkpoint information for resuming document creation"""
        checkpoint_data = {
            "collection_name": collection_name,
            "last_processed_index": index,
            "documents": documents,
            "timestamp": os.path.getmtime(checkpoint_file)
            if checkpoint_file.exists()
            else None,
        }

        with open(checkpoint_file, "wb") as f:
            pickle.dump(checkpoint_data, f)

    def _load_checkpoint(self, collection_name: str) -> Optional[int]:
        """Load checkpoint information for resuming imports"""
        checkpoint_dir = Path(
            os.getenv("TYPESENSE_CHECKPOINT_DIR", "/tmp/typesense_checkpoints")
        )
        checkpoint_file = checkpoint_dir / f"{collection_name}_checkpoint.pkl"

        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, "rb") as f:
                    checkpoint_data = pickle.load(f)

                if checkpoint_data.get("collection_name") == collection_name:
                    return checkpoint_data.get("last_processed_index", 0)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Error loading checkpoint: {str(e)}")
                )

        return 0

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            required=True,
            help="Model to index in format 'app_label.model_name' (e.g., 'myapp.Person')",
        )
        parser.add_argument(
            "--collection-class",
            type=str,
            required=True,
            help="Collection class to use in format 'module.submodule.ClassName' (e.g., 'myapp.typesense.PersonCollection')",
        )
        parser.add_argument(
            "--query",
            type=str,
            help="Optional query filter in format 'field=value' or JSON (e.g., 'status=active')",
            default=None,
        )
        parser.add_argument(
            "--query-exclude",
            type=str,
            help="Optional query filter in format 'field=value' or JSON (e.g., 'status=active') to exclude objects.",
            default=None,
        )
        parser.add_argument(
            "--export-dir",
            type=str,
            help="Directory to export schema and documents as JSON files",
            default=None,
        )
        parser.add_argument(
            "--export-only",
            action="store_true",
            help="Only export files without updating Typesense index",
            default=False,
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            help="Resume indexing from the last checkpoint",
            default=False,
        )
        parser.add_argument(
            "--force-restart",
            action="store_true",
            help="Force restart indexing from the beginning, ignoring checkpoints",
            default=False,
        )

    def export_to_json(
        self, export_dir: str, collection_name: str, schema: Dict, documents: list
    ) -> None:
        """
        Export schema and documents to JSON files
        """
        os.makedirs(export_dir, exist_ok=True)

        # Export schema
        schema_file = os.path.join(export_dir, f"{collection_name}_schema.json")
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        self.stdout.write(f"Exported schema to {schema_file}")

        # Export documents
        docs_file = os.path.join(export_dir, f"{collection_name}_documents.json")
        with open(docs_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        self.stdout.write(f"Exported {len(documents)} documents to {docs_file}")

    def handle(self, *args, **options):
        model_path = options["model"]
        query = options["query"]
        query_exlude = options["query_exclude"]

        try:
            app_label, model_name = model_path.split(".")
            model = apps.get_model(app_label, model_name)
        except ValueError:
            raise CommandError(
                'Model must be specified in format "app_label.model_name"'
            )
        except LookupError:
            raise CommandError(f"Model {model_path} not found")

        # Start with all objects
        queryset = model.objects.all()

        # Apply filter if provided
        if query or query_exlude:
            for q_key, q_value in {"filter": query, "exclude": query_exlude}.items():
                if q_value is None:
                    continue
                try:
                    # Try to parse as JSON first
                    filter_method = getattr(queryset, q_key)
                    try:
                        filter_dict = json.loads(q_value)
                        queryset = filter_method(**filter_dict)
                    except json.JSONDecodeError:
                        # Fall back to simple key=value parsing
                        if "=" in q_value:
                            key, value = q_value.split("=", 1)
                            filter_kwargs = {key.strip(): value.strip()}
                            queryset = filter_method(**filter_kwargs)
                        else:
                            raise CommandError(f"Invalid query format: {query}")
                except Exception as e:
                    raise CommandError(f"Error applying query filter: {str(e)}")

        self.stdout.write(f"Found {queryset.count()} objects to index")

        # Import the collection class dynamically
        try:
            module_path, class_name = options["collection_class"].rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            collection_class = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            raise CommandError(f"Error importing collection class: {str(e)}")

        # Initialize the collection with the queryset
        try:
            # Initialize collection and get schema
            queryset = queryset.prefetch_related(
                "personinstitution", "personperson", "personplace", "label_set"
            )
            collection = collection_class(queryset=queryset)
            schema = collection.get_schema()
            self.stdout.write(
                f"Serializing index {collection.__class__.__name__} with {schema}"
            )

            # Create checkpoint directory if it doesn't exist
            checkpoint_dir = Path(
                os.getenv("TYPESENSE_CHECKPOINT_DIR", "/tmp/typesense_checkpoints")
            )
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            collection_name = schema["name"]
            checkpoint_file = (
                checkpoint_dir / f"{collection_name}_documents_checkpoint.pkl"
            )

            # Check if we should resume document creation from a checkpoint
            documents = []
            start_obj_index = 0
            total_objects = queryset.count()

            if (
                options["resume"]
                and not options["force_restart"]
                and checkpoint_file.exists()
            ):
                try:
                    with open(checkpoint_file, "rb") as f:
                        checkpoint_data = pickle.load(f)

                    if checkpoint_data.get("collection_name") == collection_name:
                        documents = checkpoint_data.get("documents", [])
                        start_obj_index = checkpoint_data.get("last_processed_index", 0)

                        if start_obj_index > 0 and start_obj_index < total_objects:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Resuming document creation from object {start_obj_index}/{total_objects}"
                                )
                            )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Error loading document checkpoint: {str(e)}"
                        )
                    )
                    documents = []
                    start_obj_index = 0

            # If we don't have all documents yet, continue creating them
            if len(documents) < total_objects:
                # Get the queryset slice we need to process
                if start_obj_index > 0:
                    remaining_queryset = queryset[start_obj_index:]
                else:
                    remaining_queryset = queryset

                # Process in batches to create documents
                batch_size = int(os.getenv("TYPESENSE_DOC_CREATION_BATCH", "100"))

                for i in range(0, remaining_queryset.count(), batch_size):
                    batch_queryset = remaining_queryset[i : i + batch_size]
                    try:
                        # Create a temporary collection for this batch
                        batch_collection = collection_class(queryset=batch_queryset)
                        batch_documents = batch_collection.get_documents()
                        documents.extend(batch_documents)

                        # Update progress
                        current_index = start_obj_index + i + len(batch_queryset)
                        self.stdout.write(
                            f"Created documents for {current_index}/{total_objects} objects"
                        )

                        # Save checkpoint after each batch
                        self._save_documents_checkpoint(
                            checkpoint_file, collection_name, current_index, documents
                        )
                    except Exception as e:
                        # Save checkpoint at the point of failure
                        current_index = start_obj_index + i
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error during document creation at index {current_index}: {str(e)}"
                            )
                        )
                        self._save_documents_checkpoint(
                            checkpoint_file, collection_name, current_index, documents
                        )
                        raise CommandError(f"Error creating documents: {str(e)}")

            self.stdout.write(f"Generated {len(documents)} documents for indexing")

            # Export to JSON if requested
            if options["export_dir"]:
                self.export_to_json(
                    options["export_dir"], schema["name"], schema, documents
                )

            # Update Typesense index unless export-only is specified
            if not options["export_only"]:
                # Get Typesense client
                client = self.get_client()

                # Create or update collection
                self.create_or_update_collection(client, schema)

                # Import documents (no need to resume here as we already have all documents)
                collection_name = schema["name"]

                # For upload, we'll use a separate checkpoint file
                upload_checkpoint_file = (
                    checkpoint_dir / f"{collection_name}_upload_checkpoint.pkl"
                )
                start_index = 0

                # Check if we should resume from an upload checkpoint
                if options["resume"] and not options["force_restart"]:
                    # Try to load upload checkpoint
                    checkpoint_dir = Path(
                        os.getenv(
                            "TYPESENSE_CHECKPOINT_DIR", "/tmp/typesense_checkpoints"
                        )
                    )
                    upload_checkpoint_file = (
                        checkpoint_dir / f"{collection_name}_upload_checkpoint.pkl"
                    )

                    if upload_checkpoint_file.exists():
                        try:
                            with open(upload_checkpoint_file, "rb") as f:
                                checkpoint_data = pickle.load(f)

                            if (
                                checkpoint_data.get("collection_name")
                                == collection_name
                            ):
                                start_index = checkpoint_data.get(
                                    "last_processed_index", 0
                                )

                                if start_index > 0 and start_index < len(documents):
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"Resuming upload from document {start_index}/{len(documents)}"
                                        )
                                    )
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Error loading upload checkpoint: {str(e)}"
                                )
                            )
                            start_index = 0

                # Import documents
                self.import_documents(client, collection_name, documents, start_index)
        except Exception as e:
            raise CommandError(f"Error processing collection: {str(e)}")

        self.stdout.write(self.style.SUCCESS("Successfully updated index"))
