import os
from django.core.management.base import BaseCommand, CommandError
from viecpro_typesense.viecpro_workflow import main


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--detail-only",
            action="store_true",
            help="Only update detail collections",
        )
        parser.add_argument(
            "--search-only",
            action="store_true",
            help="Only update search collections",
        )
        parser.add_argument("--num", type=int)

    def handle(self, *args, **options):
        if num := options.get("num", False):
            os.environ["NUM"] = str(num)
            print(f"Working with {num} results")
        main(send=True, local=True, *args, **options)
