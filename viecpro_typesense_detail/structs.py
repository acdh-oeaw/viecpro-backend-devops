from dataclasses import dataclass
from typing import Dict
from viecpro_typesense import O


@dataclass
class Field:
    name: str
    options: O


@dataclass
class TypesenseStruct:
    name: str
    ts_type: str


@dataclass
class EntityStruct:
    entity: str
    json: TypesenseStruct


@dataclass
class NestedStruct:
    name: str
    ts_type: str
    json: Dict[str, TypesenseStruct]


confession = TypesenseStruct("confession", "string[]")
collected_titles = TypesenseStruct("collected_titles", "string[]")
first_marriage = TypesenseStruct("first_marriage", "object")
married_name = TypesenseStruct("married_name", "string")


core_info = NestedStruct("core_info", "object", {
    "confession": confession,
    "collected_titles": collected_titles,
    "first_marriage": first_marriage,
    "married_name": married_name
})

duplicates = TypesenseStruct("duplicates", "object[]")

sections = NestedStruct("sections", "object", {
    "duplicates": duplicates,
    "alt_names": [],
    "titles_honor": [],
    "titles_academic": [],
    "sources": [],
    "functions_court": [],
    "person_relations_court": [],
    "other_relations_court": [],
    "marriages_and_personal_relations": [],
    "church_and_order_relations": [],
    "functions_other": []
})


old = {
    "core-info":
    {
        "confession": "",
        "collected_titles": "",
        "first_marriage": "",
        "married_name": "",
    },
    "sections": {
        "duplicates": [],
        "alt_names": [],
        "titles_honor": [],
        "titles_academic": [],
        "sources": [],
        "functions_court": [],
        "person_relations_court": [],
        "other_relations_court": [],
        "marriages_and_personal_relations": [],
        "church_and_order_relations": [],
        "functions_other": []

    }

}
