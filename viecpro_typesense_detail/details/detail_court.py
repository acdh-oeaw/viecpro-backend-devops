from .utils import F, C, ampel
from apis_core.apis_entities.models import Institution
from typing import Dict, Any, List, TypeVar
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass
from viecpro_typesense_detail.details.utils import (
    format_and_orient_relation,
    get_references_for_instance,
    to_rel,
)
from apis_core.apis_labels.models import Label

"""

# Header: 

Datenblatt {Hofstaat}
{court.kind} {if label kategorie } {label kategorie} 
{court.fullnamename} | {court.name}


# Stammdaten

Name: 
Auflösung: 
Kategorie:
Laufzeit:
VieCPro ID:

# Left Sections

Alternative Bezeichnungen:

Download und Zitierweise:


Quellenbelege:


# Right Sections:

Inhaber*innen: rel person institution "war Hofstaat von [Reverse]"  | "gehörte"
Personalliste: all other perinst rels
Standorte: Institution Placce
Hierarchie: InstitutionInstitution rel data
"""


# each field in the collection directly corresponds to a section of data in the detail page
court_fields = [
    # if no type is given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    F("start_date", type="string"),
    F("end_date", type="string"),
    F("resolution", type="string"),
    F("category", type="string"),
    F("alternative_names"),
    F("owners"),
    F(
        "sources"
    ),  # TODO: give robin example of how to display sources, and format this accordingly
    F("personnel"),
    F("locations"),
    F("hierarchy"),
    F("notes", type="string"),
]


def parse_court_relations(i: Institution, res: Dict[str, Any]) -> Dict[str, Any]:
    rel: Any
    for rel in i.get_related_relation_instances():
        model_name = rel.__class__.__name__

        if rel.get_related_entity_instanceB() == i:
            res["hierarchy"].append(format_and_orient_relation(rel, reverse=True))
        else:
            res["hierarchy"].append(format_and_orient_relation(rel))

        if model_name == "PersonInstitution":
            if rel.relation_type.name in [
                "hatte den Hofstaat",
            ]:
                res["owners"].append(format_and_orient_relation(rel, reverse=True))
            else:
                # Note: relation needs to be reversed, as institution is always in target position, but we want the related person
                res["personnel"].append(format_and_orient_relation(rel, reverse=True))

        if model_name == "InstitutionPlace":
            res["locations"].append(format_and_orient_relation(rel))

    return res


def parse_court_labels(i: Institution, res: Dict[str, Any]) -> Dict[str, Any]:
    label: Label
    for label in i.label_set.all():
        match label.label_type.name:
            case "name":
                res["alternative_names"].append(to_rel(label))
            case "Bezeichnung, alternativ":
                res["alternative_names"].append(to_rel(label))
            case "Kategorie":
                res["category"] = label.label
            case "Auflösung":
                res["resolution"] = label.label

    return res


def main(offset: int = 0) -> Dict[str, Any]:
    ts_collection = C(name="viecpro_v2_detail_court", fields=court_fields)
    schema = ts_collection.to_schema()

    results = []
    model = Institution
    # TODO: filter only courts from the institution-model
    data = model.objects.filter(kind__name="Hofstaat")

    count = len(data)
    for idx, instance in enumerate(data):
        if idx < offset:
            continue

        if idx % 100 == 0:
            print(f"{idx}/{count}")

        res = ts_collection.to_empty_result_dict()

        res["id"] = f"{instance.id}"
        res["model"] = model.__name__
        res["object_id"] = str(instance.id)
        res["name"] = instance.name
        res["start_date"] = instance.start_date_written
        res["end_date"] = instance.end_date_written
        res = parse_court_labels(instance, res)
        res = parse_court_relations(instance, res)
        # NOTE: sources contain the bibtex json directly, they could be parsed to a) conform to the naming scheme and b) get rid of uneccessary data
        res["sources"] = get_references_for_instance(instance)
        res["status"] = ampel(instance)
        res["sameAs"] = [
            uri.uri
            for uri in instance.uri_set.all()
            if not uri.uri.startswith("https://viecpro.acdh.oeaw.ac.at")
        ]
        res["notes"] = instance.notes if instance.notes else ""

        results.append(res)

    return {"schema": schema, "results": results}
