from .utils import F, C
from apis_core.apis_entities.models import Institution
from typing import Dict, Any, List
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass



# each field in the collection directly corresponds to a section of data in the detail page
court_fields = [
    # if no type is given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    # TODO: add all fields


]

def parse_court_relations(c:Institution, res)->List[Any]: 
    """
    parse for: 

    """

    
    return res


def parse_court_labels(c:Institution, res)->List[Any]: 
    """
    parse for: 

  
    """

    return res

def main(offset:int=0) -> Dict[str, Any]: 
    c = C(name="viecpro_detail_court", fields=court_fields)
    schema = c.to_schema()

    results = []
    model = Institution 
    # TODO: filter only courts from the institution-model
    data = model.objects.all()

    count = len(data)
    for idx, instance in enumerate(data): 
        if idx < offset: 
            continue

        if idx % 100 == 0:
            print(f"{idx}/{count}")

        res = c.to_empty_result_dict()
        res = parse_court_labels(instance, res)
        res = parse_court_relations(instance, res)
        res["id"] = f"detail_{model._meta.model_name}_{instance.id}"
        res["object_id"] = str(instance.id)
        res["model"] = model.__name__
        results.append(res)

    return {"schema":schema, "results":results}
