from django.core.management.base import BaseCommand, CommandError
import argparse

class Command(BaseCommand):
    collection_choices = ["all", "single"]
    
    def add_arguments(self, parser):
        parser.add_argument("-w", "--write", action="store_true", dest="write", default=False)
        parser.add_argument("-nw", "--no-write", action="store_false", dest="write")
        parser.add_argument("-c", "--collections", choices=self.collection_choices, default="all", type=str)

        pass

    def handle(self, *args, **options):
        self.stdout.write("starting")
        self.stdout.write(f"{args=}, {options=}")
    
        self.stdout.write("finished")
        

    
