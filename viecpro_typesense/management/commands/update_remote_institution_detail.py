from django.core.management.base import BaseCommand, CommandError
from viecpro_typesense_detail.details.detail_institution import main
from viecpro_typesense.clients import local_client, remote_client


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        pass

    def handle(self, *args, **options):
        client = remote_client



        institution_detail_data = main()
        institution_detail_schema = institution_detail_data["schema"]
        institution_detail_docs = institution_detail_data["results"]

        try:
            client.collections[institution_detail_schema["name"]].delete()
        except Exception as e:
            pass

   
        client.collections.create(institution_detail_schema)
        client.collections[institution_detail_schema["name"]].documents.import_(
            institution_detail_docs, {"action": "create"}
        )

