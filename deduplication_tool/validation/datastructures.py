from pydantic import BaseModel, AfterValidator, model_validator
from typing import  TypedDict
from typing_extensions import Annotated
from apis_core.apis_entities.models import Person
from dubletten_tool.models import *
from deduplication_tool.validation.validation_functions import is_person_with_proxy, check_person_proxy_status, is_group

PersonId = Annotated[int, AfterValidator(is_person_with_proxy)]
GroupId = Annotated[int, AfterValidator(is_group)]

class SelectionPerson(BaseModel): 
    person_id: PersonId

class SelectionMember(SelectionPerson): 
    @model_validator(mode="after")    
    def check_personproxy_status(self):
       return check_person_proxy_status(instance=self, expected_status="candidate")
    
class SelectionSingle(SelectionPerson): 
    @model_validator(mode="after")    
    def check_personproxy_status(self):
        return check_person_proxy_status(instance=self, expected_status="single")

class SelectionGroup(BaseModel): 
    group_id: GroupId
    members: list[SelectionMember]
    
    @model_validator(mode="after")    
    def check_members_are_members_of_group(self): 
        members = Person.objects.filter(id__in=[el.person_id for el in self.members])
        for m in members: 
            assert m.personproxy.group_set.all().count() == 1, f"Person with id={m.id} is member in groups={m.personproxy.group_set.all()}." # type: ignore
            assert m.personproxy.group_set.first().id == self.group_id, f"Person with id={m.id} is no member in group" # type: ignore
        return self

class SelectionState(BaseModel): 
    groups: list[SelectionGroup]
    singles: list[SelectionSingle]

class RawSelectionState(TypedDict):
    groups: dict[str,list[int]]
    singles: list[int]


