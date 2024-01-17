from .utils import F, C
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
    # TODO: add all fields


]

def parse_place_relations(p:Place, res)->List[Any]: 
    """
    parse for: 

    """

    
    return res


def parse_place_labels(p:Place, res)->List[Any]: 
    """
    parse for: 

  
    """

    return res

def main(offset:int=0) -> Dict[str, Any]: 
    c = C(name="viecpro_detail_place", fields=court_fields)
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
        results.append(res)

    return {"schema":schema, "results":results}
