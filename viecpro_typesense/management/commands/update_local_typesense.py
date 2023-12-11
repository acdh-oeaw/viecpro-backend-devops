from django.core.management.base import BaseCommand, CommandError
from viecpro_typesense.viecpro_workflow import main


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        pass

    def handle(self, *args, **options):
        main(send=True)
