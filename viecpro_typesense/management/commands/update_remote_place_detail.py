from django.core.management.base import BaseCommand, CommandError
from viecpro_typesense_detail.details.detail_place import main
from viecpro_typesense.clients import local_client, remote_client


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        pass

    def handle(self, *args, **options):
        client = remote_client

        place_detail_data = main()
        place_detail_schema = place_detail_data["schema"]
        place_detail_docs = place_detail_data["results"]

        try:
            client.collections[place_detail_schema["name"]].delete()
        except Exception as e:
            pass

        client.collections.create(place_detail_schema)
        client.collections[place_detail_schema["name"]].documents.import_(
            place_detail_docs, {"action": "create"}
        )

