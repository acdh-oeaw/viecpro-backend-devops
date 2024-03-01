# This init file takes care of shared dependencies in all classes,
# it also takes care of interdependent classes by resolving the import order
# and it also takes care of injecting dependent classes into other classes

# shared imports
from collections import defaultdict, Counter
from enum import Enum
from apis_core.apis_entities.models import Person, AbstractEntity
from apis_core.apis_relations.models import AbstractRelation, PersonPerson
from apis_core.apis_vocabularies.models import PersonPersonRelation, LabelType
from apis_core.apis_metainfo.models import Collection, Label
from dubletten_tool.models import Group, PersonProxy
from apis_ampel.models import AmpelTemp
import pandas as pd

from time import time

rt_vorfin, c = PersonPersonRelation.objects.get_or_create(
            name="data merged from", name_reverse="merged into"
        )
# this is just a dummy to resolve imports
log = print
class LoggerDummy:
     exception = print

logger = LoggerDummy


# helper functions
from dubletten_tool.src.functions.helper_functions import get_group, is_dublette, get_ampel, function_timer
# ordered imports of dependent classes
from .ErrorLoggerMixin import ErrorLoggerMixin

# Helper must be imported before Type
from .PersonHelper import PersonHelper
from .PersonType import PersonType

# set enum in PersonHelper for error logging:
PersonHelper.enum = PersonType


# Helper must be imported before Kind
from .PPHelper import PPHelper
from .PPKind import PPKind


# This static fields in PPHelper use the PPKind Enum above, so they need to be added after the class is initialised
# Mapping between the PersonType of A- and B- side of PP -rels and their PPKind formal representation.
# TODO: does not include all possible connections and outcomes
PPHelper._kindmap = {
    (PersonType.DUBLETTE, PersonType.SINGLE): PPKind.DUBSING,
    (PersonType.SINGLE, PersonType.DUBLETTE): PPKind.SINGDUB,
    (PersonType.VORFIN, PersonType.VORFIN): PPKind.VORVOR,
    (PersonType.SINGLE, PersonType.VORFIN): PPKind.SINGVOR,
    (PersonType.VORFIN, PersonType.SINGLE): PPKind.VORSING,
    (PersonType.SINGLE, PersonType.SINGLE): PPKind.SINGSING,
    (PersonType.DUBLETTE, PersonType.VORFIN): PPKind.DUBVOR,
    (PersonType.VORFIN, PersonType.DUBLETTE): PPKind.VORDUB,
    # VORSAME not included in mapping as the mapping is only used in creating new relations for groups
    # that are to be remerged - i.e. no vorfin entries exist there.

}

# Mapping between initial kind of relation and the expected 'correct' kind of created relations from them.
# Used to check against and raise errors if expectation is not matched during writing of the relations.
PPHelper._expectation = {
    PPKind.DUBSING.name: [PPKind.VORSING],
    PPKind.SINGDUB.name: [PPKind.SINGVOR],
    PPKind.VORVOR.name: [PPKind.VORVOR],
    PPKind.SINGVOR.name: [PPKind.SINGVOR],
    PPKind.VORSING.name: [PPKind.VORSING],
    PPKind.SINGSING.name: [PPKind.SINGSING],
    PPKind.DUBVOR.name: [PPKind.VORVOR],
    PPKind.VORDUB.name: [PPKind.VORVOR],
    PPKind.DUBDUB.name: [PPKind.VORVOR, PPKind.VORSAME],
    PPKind.DUBSAME.name: [PPKind.VORSAME],
}


# set enum in PPHelper for error logging:
PPHelper.enum = PPKind



from .ProcessingTracker import ProcessingTracker
from .RelationWriter import RelationWriter
from .TempRel import TempRel
from .MergeGroup import MergeGroup
