from django.core.management.base import BaseCommand, CommandError
from viecpro_typesense_detail.details.detail_court import main
from viecpro_typesense.clients import local_client, remote_client


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        pass

    def handle(self, *args, **options):
        client = remote_client

        court_detail_data = main()
        court_detail_schema = court_detail_data["schema"]
        court_detail_docs = court_detail_data["results"]

        try:
            client.collections[court_detail_schema["name"]].delete()
        except Exception as e:
            pass

        client.collections.create(court_detail_schema)
        client.collections[court_detail_schema["name"]].documents.import_(
            court_detail_docs, {"action": "create"}
        )

