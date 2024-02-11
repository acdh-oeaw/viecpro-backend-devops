from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any
from apis_core.apis_labels.models import Label
from django.contrib.contenttypes.models import ContentType
from apis_bibsonomy.models import Reference  # type: ignore
from apis_core.apis_relations.models import AbstractRelation
import json 

@dataclass
class F:
    """
    Represents a Typesense field with default options.

    methods: 

        to_dict(self)
            returns the instance as a dict
        to_empty_result_dict(self)
            returns a dict with the field-instance-name as key and an empty datastructure as value
            dependendend on the type of the field
    """
    name: str
    type: str = "object[]"
    optional: bool = True
    sort: bool = False
    facet: bool = False
    index: bool = False

    def to_dict(self):
        return asdict(self)

    def to_empty_result_dict(self) -> Dict[str, Any]:
        return {self.name: [] if "[]" in self.type else {} if self.type == "object" else ""}


@dataclass
class C:
    """
    Represents a Typesense collection.

    methods: 
        to_schema(self)
            returns the instance as a dict
        to_empty_result_dict(self)
            returns a dict that contains all field-names as keys with an empty datastructure as value
            dependend on the type of the field. used to build an instances document.
    """
    name: str
    enable_nested_fields: bool = True
    fields: List[F] = field(default_factory=list)

    def to_schema(self):
        schema = asdict(self)
        return schema

    def to_empty_result_dict(self):
        return {k: v for f in self.fields for k, v in f.to_empty_result_dict().items()}




def to_rel(l:Label)-> Dict[str, Any]:
    """
    Helper that maps a label to a kind of relation-like datastructure. 
    Note that the name of the fields are changed.
    """
    return {"name": l.label, "start_date": l.start_date_written or "", "end_date": l.end_date_written or ""}




def format_and_orient_relation(rel: AbstractRelation, reverse:bool=False)-> Dict[str, Any]:
    """
    Returns a nested structure that represents a relation. Maps keys and re-orients the relation
    if the reverse flag is set.

    Background:
    Relations are oriented from entity a to b. In the ui, they are shown always from the 
    view of the selected entity, i.e. with the selected entity in A-position (subject if you will).
    So if a relation has the selected entity in target position, it gets reversed here.
    """
    if reverse:
        target_entity = getattr(rel, rel.get_related_entity_field_nameA())  # type: ignore
        relation_type = rel.relation_type.name_reverse  # type: ignore
    else:
        target_entity = getattr(rel, rel.get_related_entity_field_nameB())  # type: ignore
        relation_type = rel.relation_type.name  # type: ignore
    target = {
        "name": str(target_entity),
        "object_id": str(target_entity.id),
        "model": str(target_entity.__class__.__name__)}

    return {"relation_type": relation_type, "target": target, "start_date": rel.start_date_written or "", "end_date": rel.end_date_written or ""}



def get_references_for_instance(instance:Any)-> List[Dict[str, Any]]:
    ct = ContentType.objects.get_for_model(instance._meta.model)
    references = Reference.objects.filter(content_type=ct, object_id=instance.id)
    if not references: 
        return []
    else: 
        return [{
            "start_page": r.pages_start,
            "end_page": r.pages_end,
            "folio": r.folio,
            "bibtex":  "null" if not r.bibtex else json.loads(r.bibtex),
            } for r in references]

