from .utils import F, C
from typing import Dict, Any, List, Union, Iterable
from apis_bibsonomy.models import Reference
from django.contrib.contenttypes.models import ContentType
import json

"""
"""

# each field in the collection directly corresponds to a section of data in the detail page
reference_fields = [
    # Not that sources do not exist as a seperate model, so the model field is not included in this collection
    F("id", type="string", index=True, optional=False),
    # NOTE decided with Robin not to include the model field here; if this causes issues, here is the place to fix it
    F("object_id", type="string", index=True, optional=False),
    F("short_title", type="string"),
    F("title", type="string"),
    F("type", type="string"),
    F("bibtex", type="string"),
    F("references")

]

def parse_source_references(references:Iterable[Reference], res:Dict[str, Any])->Dict[str, Any]: 
    """
    """
    def get_generic_object(content_type:ContentType, object_id:Union[str, int])->Any:
        return content_type.model_class().objects.get(id=object_id) # type: ignore
    
    def create_target_entity(target:Any):
        return {
        "name": str(target),
        "object_id": str(target.id),
        "model": str(target.__class__.__name__)}
        # Consider adding disction here 
    
    def create_relation(r:Reference):
        target_entity = create_target_entity(get_generic_object(r.content_type, r.object_id))
        return {"folio":r.folio, "target_entity": target_entity}


    for ref in references:
        if ref.folio:
            res["references"].append(create_relation(ref))
        
    return res


def parse_source_meta(reference:Reference, res:Dict[str, Any])->Dict[str, Any]: 
    """
    """
    bibtex = json.loads(reference.bibtex) 
    res["id"] = f"detail_source_{reference.bibs_url}"
    res["short_title"] = bibtex.get("shortTitle")
    res["title"] = bibtex.get("title", "")
    res["type"] = bibtex.get("type", "")
    res["bibtex"] = bibtex

    return res

def main(offset:int=0) -> Dict[str, Any]: 
    ts_collection = C(name="viecpro_detail_source", fields=reference_fields)
    schema = ts_collection.to_schema()

    results:List[Any] = []
    model = Reference 
    data = model.objects.values_list("bibs_url", flat=True).distinct() 

    count = len(data)
    for idx, source_url in enumerate(data): 
        if idx < offset: 
            continue
        try:
            refs = model.objects.filter(bibs_url=source_url)
            res: dict[str, Any] = ts_collection.to_empty_result_dict()
            res = parse_source_meta(refs.first(), res)
            res = parse_source_references(refs, res) 

            if idx % 100 == 0:
                print(f"{idx}/{count}")
            if len(res) > 1:
                results.append(res)

        except Exception as e: 
            print(e)
            continue
        

    return {"schema":schema, "results":results}
