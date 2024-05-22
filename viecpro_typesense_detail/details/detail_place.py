from .utils import F, C, format_and_orient_relation, ampel
from apis_core.apis_entities.models import Place
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List
from collections import defaultdict
from apis_core.apis_entities.models import Place
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass



# each field in the collection directly corresponds to a section of data in the detail page
place_fields = [
    # if no type is given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    F("alternative_names", type="string[]"),
    F("person_relations"),
    F("place_relations"),
    F("institution_relations"),
    F("notes", type="string")
    # TODO: add all fields


]

def parse_place_relations(p:Place, res) -> List[Any]: 
    """
    parse for: 

    """
    for rel in p.get_related_relation_instances():
        model_name = rel.__class__.__name__

        if rel.get_related_entity_instanceB() == p: 
            temp_rel = format_and_orient_relation(rel, reverse=True)
        else: 
            temp_rel = format_and_orient_relation(rel)

        if model_name == "PlacePlace": 
            res["place_relations"].append(temp_rel)
        
        if model_name == "PersonPlace": 
            res["person_relations"].append(temp_rel)

        if model_name == "InstitutionPlace": 
            res["institution_relations"].append(temp_rel)
    
    return res


def parse_place_labels(p:Place, res)->List[Any]: 
    """
    As the display of other labels than alternative names is undecided atm, the possible 
    candidates are added here but skipped.
    """
    for l in p.label_set.all().prefetch_related("label_type"):
        match l.label_type.name: 
            case "Bezeichnung, alternativ":
                res["alternative_names"].append(l.label)
            case "Bezeichnung, Adresse 1822":
                pass
            case "Bezeichnung, Suttingerstadtplan":
                pass
            case "Stadtviertel_1730":
                pass
            case "URI_p_lucienfeld_harrer":
                pass
            case "URI_wien_wiki":
                pass
    return res

def main(offset:int=0) -> Dict[str, Any]: 
    c = C(name="viecpro_detail_place", fields=place_fields)
    schema = c.to_schema()

    results = []
    model = Place 
    data = model.objects.all().prefetch_related() 

    count = len(data)
    for idx, instance in enumerate(data): 
        if idx < offset: 
            continue

        if idx % 100 == 0:
            print(f"{idx}/{count}")

        res = c.to_empty_result_dict()
        res = parse_place_labels(instance, res)
        res = parse_place_relations(instance, res)
        res["id"] = f"detail_{model._meta.model_name}_{instance.id}"
        res["object_id"] = str(instance.id)
        res["model"] = model.__name__
        res["ampel"] = ampel(instance)
        res["sameAs"] = [uri.uri for uri in instance.uri_set.all() if not uri.uri.startswith("https://viecpro.acdh.oeaw.ac.at")]
        res["notes"] = instance.notes if instance.notes else ""
        results.append(res)

    return {"schema":schema, "results":results}
