from django.core.management.base import BaseCommand, CommandParser
from viecpro_typesense_detail.details import *
from viecpro_typesense.utils import process_detail_collection
from viecpro_typesense.clients import local_client, remote_client
from typing import Dict, Any, List

collection_processing_map = {
    "person": process_detail_person_collection,
    "place": process_detail_place_collection,
    "court": process_detail_court_collection,
    "institution": process_detail_institution_collection,
    "source": process_detail_source_collection,
}


class Command(BaseCommand):
    help = "Command to update one or several detail collections on remote or local typesense server."
    collection_choices = list(collection_processing_map.keys())

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--use-remote",
            action="store_true",
            help="If set, the remote typesense index will be updated, otherwise the local instance.",
        )
        parser.add_argument(
            "collection",
            nargs="+",
            type=str,
            choices=self.collection_choices,
            help="Name of the collection entity to update. f.e. 'person' - which would update the 'viecpro_detail_person' - collection. Accepts one or multiple collections to update.",
        )

    def handle(self, *args: List[Any], **options: Dict[str, Any]):
        use_remote = options.get("use_remote")
        collections = options["collection"]

        client = local_client if not use_remote else remote_client
        if client == local_client:
            print("USING local typesense client.")
        else:
            print("USING remote client")

        for col in collections:
            col_name = col.lower()
            try:
                process_detail_collection(
                    collection_processing_map[col_name], client, send=True, col_name=col_name
                )
            except Exception as e:
                print("FAILED: ", e)
                continue
