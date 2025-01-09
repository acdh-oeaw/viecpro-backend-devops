from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
import json
import typesense
import os
from typing import Dict, Any


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
        self, client: typesense.Client, collection_name: str, documents: list
    ) -> None:
        """
        Import documents into Typesense collection with batch processing
        """
        try:
            # Configure batch size
            batch_size = int(os.getenv("TYPESENSE_BATCH_SIZE", "1000"))

            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                results = client.collections[collection_name].documents.import_(batch)

                # Check for errors in import results
                errors = [r for r in results if "error" in r]
                if errors:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Batch {i//batch_size + 1}: {len(errors)} errors in {len(batch)} documents"
                        )
                    )

                self.stdout.write(
                    f"Imported {min(i + batch_size, len(documents))}/{len(documents)} documents"
                )

        except typesense.exceptions.TypesenseClientError as e:
            raise CommandError(f"Error importing documents: {str(e)}")

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
        if query:
            try:
                # Try to parse as JSON first
                try:
                    filter_dict = json.loads(query)
                    queryset = queryset.filter(**filter_dict)
                except json.JSONDecodeError:
                    # Fall back to simple key=value parsing
                    if "=" in query:
                        key, value = query.split("=", 1)
                        filter_kwargs = {key.strip(): value.strip()}
                        queryset = queryset.filter(**filter_kwargs)
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
            # Initialize collection and get schema/documents
            queryset = queryset.prefetch_related(
                "personinstitution", "personperson", "personplace", "label_set"
            )
            collection = collection_class(queryset=queryset)
            schema = collection.get_schema()
            self.stdout.write(
                f"Serializing index {collection.__class__.__name__} with {schema}"
            )
            documents = collection.get_documents()
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

                # Import documents
                self.import_documents(client, schema["name"], documents)
        except Exception as e:
            raise CommandError(f"Error processing collection: {str(e)}")

        self.stdout.write(self.style.SUCCESS("Successfully updated index"))
