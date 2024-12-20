import os
import requests
from .utils import F, C
from typing import Dict, Any, List, Union, Iterable
from apis_bibsonomy.models import Reference
from django.contrib.contenttypes.models import ContentType
import json


# each field in the collection directly corresponds to a section of data in the detail page
reference_fields = [
    # NOTE: sources do not exist as a separate model, so the model field is not included in this collection
    F("id", type="string", index=True, optional=False),
    # NOTE decided with Robin not to include the model field here; if this causes issues, here is the place to fix it
    F("object_id", type="string", index=True, optional=False),
    F("short_title", type="string"),
    F("title", type="string"),
    F("type", type="string"),
    F("bibtex", type="string"),
    F("tag", type="string"),  # the tag group to which the source belongs
    F("references"),
]


def parse_source_references(
    references: Iterable[Reference], res: Dict[str, Any]
) -> Dict[str, Any]:
    """ """

    def get_generic_object(
        content_type: ContentType, object_id: Union[str, int]
    ) -> Any:
        return content_type.model_class().objects.get(id=object_id)  # type: ignore

    def create_target_entity(target: Any):
        return {
            "name": str(target),
            "object_id": str(target.id),
            "model": str(target.__class__.__name__),
            # TODO: make this logic uniform across all collections
            "detail_collection_name": (
                "viecpro_v2_detail_court"
                if hasattr(target, "kind") and target.kind.name == "Hofstaat"
                else f"viecpro_v2_detail_{target.__class__.__name__}"
            ),
        }

    def create_relation(r: Reference):
        target_entity = create_target_entity(
            get_generic_object(r.content_type, r.object_id)
        )
        return {"folio": r.folio, "target_entity": target_entity}

    for ref in references:
        if ref.folio:
            res["references"].append(create_relation(ref))

    return res


def get_tag_group(reference: Reference) -> str:
    """Get the tags from the Zotero API and return the tags with prefix "1_" as the tag group

    Args:
        reference (Reference): The reference object

    Returns:
        list: list of tags with prefix "1_"
    """
    json = requests.get(
        reference.bibs_url, params={"key": os.environ.get("ZOTERO_API_KEY")}
    ).json()
    tags = json["data"].get("tags")
    tag_group = [tag["tag"][2:] for tag in tags if tag["tag"].startswith("1_")]
    if len(tag_group) == 1:
        return tag_group[0]
    else:
        return "Allgemein"


def parse_source_meta(reference: Reference, res: Dict[str, Any]) -> Dict[str, Any]:
    """ """
    bibtex = json.loads(reference.bibtex)
    res["id"] = f"detail_source_{reference.bibs_url}"
    res["short_title"] = bibtex.get("shortTitle")
    res["title"] = bibtex.get("title", "")
    res["type"] = bibtex.get("type", "")
    res["tag"] = get_tag_group(reference)
    res["bibtex"] = bibtex

    return res


def main(offset: int = 0) -> Dict[str, Any]:
    ts_collection = C(name="viecpro_v2_detail_source", fields=reference_fields)
    schema = ts_collection.to_schema()

    results: List[Any] = []
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

    return {"schema": schema, "results": results}
