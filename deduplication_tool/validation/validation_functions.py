from apis_core.apis_entities.models import Person
from dubletten_tool.models import Group

from typing import Literal, Any

def is_group(id: int): 
    assert Group.objects.filter(id=id).exists(), f"Group with {id=} does not exist in database."
    return id

def is_person_with_proxy(id:int):
    assert Person.objects.filter(id=id).exists(), f"Person with {id=} does not exist in database."
    assert getattr(Person.objects.get(id=id), "personproxy") !=None, f"Person with {id=} had no personproxy."
    return id

def check_person_proxy_status(instance: Any, expected_status: Literal["candidate", "single", "merged"]):
    id = instance.person_id
    per = Person.objects.get(id=id)
    proxy = getattr(per, "personproxy")
    status = getattr(proxy, "status")

    assert status == expected_status, f"Status {status=} of person with id {id=} did not match {expected_status=}."
    return instance