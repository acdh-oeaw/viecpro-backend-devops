from django.db import models
from apis_core.apis_vocabularies.models import (
    VocabsBaseClass,
    PersonInstitutionRelation,
)
from apis_core.apis_metainfo.models import TempEntityClass


class ToplevelFunction(TempEntityClass):
    # consider inheriting from temp_entity_class to get labels auto added for category
    # name = models.CharField(max_length=256)
    subsumed_functions_set = models.ManyToManyField(
        PersonInstitutionRelation, related_name="toplevel_functions_set"
    )
    # TODO: add method to get all subsumed relations (personell)


class AlternativeFunctionName(TempEntityClass):
    # consider inheriting from temp_entity_class to get labels auto added for category
    # name = models.CharField(max_length=256)
    functions_set = models.ManyToManyField(
        PersonInstitutionRelation, related_name="alternative_names_set"
    )
