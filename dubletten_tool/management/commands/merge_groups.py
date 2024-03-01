from django.core.management.base import BaseCommand
from dubletten_tool.models import Group
from apis_core.apis_metainfo.models import Collection
import logging
from django.contrib.auth.models import User
from dubletten_tool.logger import init_logger
from apis_core.apis_metainfo.models import Collection
from dubletten_tool.models import Group
from dubletten_tool.merge_functions import write_person_person_rels, MergeGroup

log = logging.getLogger("DBLogger")

user = User.objects.get(username="GPirgie")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        merged, c = Collection.objects.get_or_create(name="Vorfinale Einträge")
        merged.tempentityclass_set.all().delete()

        gg = Group.objects.all()
        all = len(gg)
        for idx, g in enumerate(gg):
            MergeGroup(g).run_process()
            # print(f"Create Group: {idx}/{all}")

        for idx, g in enumerate(gg):
            write_person_person_rels(g)
            # print(f"Write PerPerRelation: {idx}/{all}")

        self.stdout.write("all processes finished with success")
