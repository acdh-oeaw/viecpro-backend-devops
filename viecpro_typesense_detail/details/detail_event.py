from .utils import F, C, ampel
from typing import Dict, Any, List
from apis_core.apis_entities.models import Event
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass
from viecpro_typesense_detail.details.utils import (
    format_and_orient_relation,
    get_references_for_instance,
    to_rel,
)


# each field in the collection directly corresponds to a section of data in the detail page
event_fields = [
    # if no type is given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    #     F("resolution", type="string"),
    #     F("category", type="string"),
    #     F("alternative_names"),
    #     F("sources"), # TODO: give robin example of how to display sources, and format this accordingly
    #     F("personnel"),
    #     F("locations"),
    #     F("hierarchy"),
]


def parse_event_relations(i: Event, res: Dict[str, Any]) -> Dict[str, Any]:
    # for rel in i.get_related_relation_instances():
    #     model_name = rel.__class__.__name__

    #     if rel.get_related_entity_instanceB() == i:
    #         res["hierarchy"].append(format_and_orient_relation(rel, reverse=True))
    #     else:
    #         res["hierarchy"].append(format_and_orient_relation(rel))
    #     if model_name == "PersonEvent":
    #         # Note: relation needs to be reversed, as event is always in target position, but we want the related person
    #         res["personnel"].append(format_and_orient_relation(rel, reverse=True))
    #     if model_name == "PlaceEvent":
    #         res["locations"].append(format_and_orient_relation(rel))

    # return res
    return res


def parse_event_labels(i: Event, res: Dict[str, Any]) -> Dict[str, Any]:

    # for label in i.label_set.all():
    #     match label.label_type.name:
    #         case "name":
    #             res["alternative_names"].append(to_rel(label))
    #         case "Bezeichnung, alternativ":
    #             res["alternative_names"].append(to_rel(label))
    #         case "Kategorie":
    #             res["category"] = label.label
    #         case "Auflösung":
    #             res["resolution"] = label.label

    return res


def main(offset: int = 0) -> Dict[str, Any]:
    ts_collection = C(name="viecpro_detail_event", fields=event_fields)
    schema = ts_collection.to_schema()

    results = []
    model = Event

    data = model.objects.all()

    count = len(data)
    for idx, instance in enumerate(data):
        if idx < offset:
            continue

        if idx % 100 == 0:
            print(f"{idx}/{count}")

        res = ts_collection.to_empty_result_dict()

        res["id"] = f"detail_{model._meta.model_name}_{instance.id}"
        res["model"] = model.__name__
        res["object_id"] = str(instance.id)
        res = parse_event_labels(instance, res)
        res = parse_event_relations(instance, res)
        # NOTE: sources contain the bibtex json directly, they could be parsed to a) conform to the naming scheme and b) get rid of uneccessary data
        res["sources"] = get_references_for_instance(instance)
        res["ampel"] = ampel(instance)
        res["sameAs"] = [uri.uri for uri in instance.uri_set.all() if not uri.uri.startswith("https://viecpro.acdh.oeaw.ac.at")]

        results.append(res)

    return {"schema": schema, "results": results}
