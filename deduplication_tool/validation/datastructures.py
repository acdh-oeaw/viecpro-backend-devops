from pydantic import BaseModel, AfterValidator, model_validator
from typing_extensions import Annotated
from apis_core.apis_entities.models import Person
from dubletten_tool.models import *
from deduplication_tool.validation.validation_functions import (
    is_vorfin,
    is_person_with_proxy,
    check_person_proxy_status,
    is_group,
)

PersonId = Annotated[int, AfterValidator(is_person_with_proxy)]
GroupId = Annotated[int, AfterValidator(is_group)]
VorfinId = Annotated[int, AfterValidator(is_vorfin)]


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
            assert (
                m.personproxy.group_set.all().count() == 1
            ), f"Person with id={m.id} is member in groups={m.personproxy.group_set.all()}."  # type: ignore
            assert (
                m.personproxy.group_set.first().id == self.group_id
            ), f"Person with id={m.id} is no member in group"  # type: ignore
        return self


class ActionDataRemoveMember(BaseModel):
    group_id: GroupId
    old_vorfin: VorfinId
    members_to_remove: list[PersonId]


class ActionDataDissolveGroup(BaseModel):
    group_id: GroupId
    old_vorfin: VorfinId
    old_members: list[PersonId]


class ActionDataMergeSelectedMembers(BaseModel):
    group_id: GroupId
    old_vorfin: VorfinId
    members_to_merge: list[PersonId]


class ActionDataRemergeGroup(BaseModel):
    group_id: GroupId
    old_vorfin: VorfinId


class ActionDataMergeAll(BaseModel):
    singles: list[PersonId]
    groups: list[GroupId]
    new_group_name: str


class ActionDataGroupSelected(BaseModel):
    singles: list[PersonId]
    groups: dict[GroupId, list[PersonId]]
    new_group_name: str


class ActionDataCreateGroupFromSingle(BaseModel):
    new_group_name: str
    single: PersonId


class SelectionState(BaseModel):
    """
    Models the selectionState datastructure as Objects.
    Use this in processing.
    """

    groups: list[SelectionGroup]
    singles: list[SelectionSingle]


class RawSelectionState(BaseModel):
    """
    Models the incoming json selectionState datastructure containing primitives (mostly ids).
    Use this only in the inital request parsing.
    """

    groups: dict[str, list[int]]
    singles: list[int]
