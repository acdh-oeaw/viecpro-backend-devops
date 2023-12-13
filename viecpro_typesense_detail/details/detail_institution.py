from .utils import F, C
from typing import Dict, Any, List
from apis_core.apis_entities.models import Institution 
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass



# each field in the collection directly corresponds to a section of data in the detail page
institution_fields = [
    # if no type is given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    F("resolution"),
    F("category"),
    F("duration"),
    F("alternative_names"),
    F("sources"),
    F("personnel"),
    F("locations"),
    F("hierarchy"),


]

def parse_institution_relations(i:Institution, res)->List[Any]: 
    """
    parse for: 
    - person-instituton (personnel)
    - institution-place (locations)
    - institution-institution (hierarchy)
    """

    
    return res


def parse_institution_labels(i:Institution, res)->List[Any]: 
    """
    parse for: 

    - category
    - resolution 
    - alt_names
    """

    return res

def main(offset:int=0) -> Dict[str, Any]: 
    c = C(name="viecpro_detail_institution", fields=institution_fields)
    schema = c.to_schema()

    results = []
    model = Institution 
    data = model.objects.all().prefetch_related("institutioninstitution_set", "institutionplace_set", "personinstitution_set")

    count = len(data)
    for idx, instance in enumerate(data): 
        if idx < offset: 
            continue

        if idx % 100 == 0:
            print(f"{idx}/{count}")

        res = c.to_empty_result_dict()
        res = parse_institution_labels(instance, res)
        res = parse_institution_relations(instance, res)
        res["id"] = f"detail_{model._meta.model_name}_{instance.id}"
        res["object_id"] = str(instance.id)
        res["model"] = model.__name__
        results.append(res)

    return {"schema":schema, "results":results}
