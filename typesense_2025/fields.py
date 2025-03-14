from dataclasses import dataclass, astuple, field
from os import wait
import string
from typing import List, Optional, Literal, Dict, Any, Callable
from django.db.models import Model
import re
import datetime
from django.contrib.contenttypes.models import ContentType
from functools import cache
from apis_bibsonomy.models import Reference
import json
import requests
import os


def clean_text(text):
    text = str(text)
    # Remove content within brackets and the brackets themselves
    text = re.sub(r"<[^>]+>", "", text)  # Remove <...>
    text = re.sub(r"\[[^\]]+\]", "", text)  # Remove [...]
    text = re.sub(r"\{[^\}]+\}", "", text)  # Remove {...}
    text = text.replace(" , ", ", ")
    return text.strip()


def camel_case_to_snake(string):
    field_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    field_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", field_name).lower()
    return field_name


def create_timestamps(obj):
    r1 = dict()
    if obj.start_date is not None:
        start_date = int(obj.start_date.strftime("%s"))
    else:
        start_date = int(datetime.datetime(5000, 1, 1, 0, 0).timestamp())
    if obj.end_date is not None:
        end_date = int(obj.end_date.strftime("%s"))
    else:
        end_date = int(datetime.datetime(5000, 1, 1, 0, 0).timestamp())
    r1["startDate"] = start_date
    r1["endDate"] = end_date
    r1["startDateWritten"] = (
        clean_text(obj.start_date_written)
        if obj.start_date_written is not None
        else None
    )
    r1["endDateWritten"] = (
        clean_text(obj.end_date_written) if obj.end_date_written is not None else None
    )
    return r1


def get_relation_type_str(obj, rel, post_proc=None):
    """retrieves the correct relation type string from the obj to a subj"""
    rel_cls = rel.__class__.__name__.lower()
    obj_class = obj.__class__.__name__.lower()
    attr_rel_type = "name"
    if rel_cls.startswith(obj_class) and rel_cls.endswith(obj_class):
        if getattr(rel, f"related_{obj_class}B_id") == obj.pk:
            attr_rel_type = "name_reverse"
    elif rel_cls.endswith(obj_class):
        attr_rel_type = "name_reverse"
    res = getattr(rel.relation_type, attr_rel_type)
    if post_proc is not None:
        res = post_proc(res)
    return res


@dataclass
class RelationsFieldDef:
    """Class used to store the relation definitions for the TsRelationField"""

    accessor: str
    filter: dict = field(default_factory=dict)
    exclude_filter: dict = field(default_factory=dict)
    accessor_label: Optional[str] = None
    entity_type: Optional[str | Callable] = None
    relation_types: Optional[list[str]] = None
    post_proc_rel_type: Optional[Callable] = None


# Valid Typesense field types
FieldType = Literal[
    "string",
    "int32",
    "int64",
    "float",
    "bool",
    "geopoint",
    "object",
    "string[]",
    "int32[]",
    "int64[]",
    "float[]",
    "bool[]",
    "object[]",
]


class TypesenseField:
    def __init__(
        self,
        type: FieldType,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        self.type = type
        self.facet = facet
        self.optional = optional
        self.index = index
        self.sort = sort
        self.infix = infix
        self.locale = locale
        self.num_dim = num_dim
        self.field_name = field_name

    def to_dict(self, field_name: str) -> Dict[str, Any]:
        """
        Convert the field definition to Typesense schema format
        """
        field_dict = {
            "name": field_name,
            "type": self.type,
            "facet": self.facet,
            "optional": self.optional,
            "index": self.index,
            "sort": self.sort,
            "infix": self.infix,
        }

        # Only include optional fields if they are set
        if self.locale is not None:
            field_dict["locale"] = self.locale

        if self.num_dim is not None:
            field_dict["num_dim"] = self.num_dim

        return field_dict

    def get_data_representation(self, obj: Model) -> Any:
        """
        Extract and transform data from a Django model instance

        Args:
            obj: Django model instance

        Returns:
            Processed value ready for Typesense indexing
        """
        value = getattr(obj, self.field_name, None)
        if value is None:
            return None
        if self.type in ["int32", "int64"]:
            return int(value)
        if self.type == "float":
            return float(value)
        text = clean_text(value)
        return text

    @classmethod
    def string(cls, **kwargs) -> "TypesenseField":
        """Factory method for string fields"""
        return cls(type="string", **kwargs)

    @classmethod
    def int32(cls, **kwargs) -> "TypesenseField":
        """Factory method for int32 fields"""
        return cls(type="int32", **kwargs)

    @classmethod
    def int64(cls, **kwargs) -> "TypesenseField":
        """Factory method for int64 fields"""
        return cls(type="int64", **kwargs)

    @classmethod
    def float(cls, **kwargs) -> "TypesenseField":
        """Factory method for float fields"""
        return cls(type="float", **kwargs)

    @classmethod
    def bool(cls, **kwargs) -> "TypesenseField":
        """Factory method for boolean fields"""
        return cls(type="bool", **kwargs)

    @classmethod
    def string_array(cls, **kwargs) -> "TypesenseField":
        """Factory method for string array fields"""
        return cls(type="string[]", **kwargs)


class TsFieldGender(TypesenseField):
    def get_data_representation(self, obj: Model) -> Any:
        if obj.gender == "male":
            return "männlich"
        elif obj.gender == "female":
            return "weiblich"
        else:
            return "unbekannt"


class TsFieldTimestamp(TypesenseField):
    def get_data_representation(self, obj: Model) -> Any:
        # field_name = camel_case_to_snake(self.field_name)
        date = getattr(obj, self.field_name, None)
        if date is not None:
            return int(date.strftime("%s"))
        else:
            return int(datetime.datetime(5000, 1, 1, 0, 0).timestamp())

    def __init__(
        self,
        type: FieldType,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
        include_relations: bool = False,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.include_relations = include_relations


class TsStatusField(TypesenseField):
    def get_data_representation(self, obj: Model) -> Any:
        if hasattr(obj, "ampel"):
            ampel = obj.ampel
        else:
            return "rot"
        if ampel.status == "green":
            return "grün"
        elif ampel.status == "yellow":
            return "gelb"
        else:
            return "rot"


class TsFixedStringField(TypesenseField):
    def __init__(
        self,
        type: FieldType,
        string: str,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.string = string

    def get_data_representation(self, obj: Model) -> Any:
        return self.string


class TsRelationFlatField(TypesenseField):
    def __init__(
        self,
        type: FieldType,
        accessor: str,
        filter: Optional[dict] = {},
        many: bool = True,
        use_str_method: bool = False,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.accessor = accessor
        self.filter = filter
        self.many = many
        self.use_str_method = use_str_method

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        lst_accessor = self.accessor.split(".")
        qs_attr = lst_accessor.pop(0)
        for obj1 in getattr(obj, qs_attr).filter(**self.filter):
            for acc in lst_accessor:
                obj1 = getattr(obj1, acc)
            if self.use_str_method:
                obj1 = str(obj1)
            res.append(obj1)
        if len(res) == 0 and self.optional:
            return None
        if self.many:
            return res
        else:
            return res[0]


class TsRelationField(TypesenseField):
    def __init__(
        self,
        type: FieldType,
        labels: Optional[List[str]] = None,
        relations: Optional[List[RelationsFieldDef]] = None,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.labels = labels
        self.relations = relations

    @classmethod
    @cache
    def get_vocabs_list(cls, c, term):
        res = []
        if ("A" in c or "B" in c) and "person" in c:
            mdl = "PersonPersonRelation".lower()
        elif ("A" in c or "B" in c) and "institution" in c:
            mdl = "InstitutionInstitutionRelation".lower()
        else:
            mdl = c.replace("_set", "")
        ct = ContentType.objects.get(app_label="apis_vocabularies", model=mdl)
        mc = ct.model_class()
        t1 = mc.objects.get(name=term)
        res.append(t1)
        pc = mc.objects.filter(parent_class=t1)
        while pc.count() > 0:
            res.extend([p1 for p1 in pc])
            pc = mc.objects.filter(parent_class__in=pc)
        return res

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        if self.labels is not None:
            for label in obj.label_set.filter(label_type__name__in=self.labels):
                r1 = {"relationType": label.label}
                time_data = create_timestamps(label)
                r1.update(time_data)
                res.append(r1)
        if self.relations is not None:
            for rel_type_class in self.relations:
                (
                    acc,
                    filter,
                    excl_filter,
                    acc_label,
                    entity_type,
                    rel_types,
                    post_proc_rel_type,
                ) = astuple(rel_type_class)
                lst_accessor = acc.split(".")
                if acc_label is not None:
                    lst_accessor_label = acc_label.split(".")
                qs_attr = lst_accessor.pop(0)
                if rel_types is not None:
                    if "A" in qs_attr or "B" in qs_attr:
                        mdl = "PersonPersonRelation".lower()
                    mdl = qs_attr.replace("_set", "")
                    if isinstance(rel_types, str):
                        rel_types = [rel_types]
                    rel_types_list = []
                    for r in rel_types:
                        rel_types_list.extend(self.get_vocabs_list(mdl, r))
                    filter.update({"relation_type__in": rel_types_list})
                for obj2 in (
                    getattr(obj, qs_attr).filter(**filter).exclude(**excl_filter)
                ):
                    obj1 = obj2
                    for acc in lst_accessor:
                        obj1 = getattr(obj1, acc)
                    r1 = {"id": obj1.pk}
                    if entity_type is not None:
                        if callable(entity_type):
                            kind = entity_type(obj1)
                            if kind is not None:
                                r1["kind"] = kind
                            else:
                                r1["kind"] = obj1.__class__.__name__.lower()
                        else:
                            r1["kind"] = entity_type
                    else:
                        r1["kind"] = obj1.__class__.__name__.lower()
                    label = obj1
                    if acc_label is not None:
                        for acc in lst_accessor_label:
                            label = getattr(label, acc)
                    r1["name"] = clean_text(str(label))
                    r2 = {
                        "relationType": get_relation_type_str(
                            obj, obj2, post_proc_rel_type
                        ),
                        "target": r1,
                    }
                    time_data = create_timestamps(obj2)
                    r2.update(time_data)
                    res.append(r2)
        if len(res) == 0 and self.optional:
            return None
        return res


class TsRelatedEntitiesField(TypesenseField):
    def __init__(
        self,
        type: FieldType,
        accessor: str,
        accessor_label: str,
        many: bool = False,
        filter: Optional[dict] = {},
        entity_type: Optional[str] = None,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.accessor = accessor
        self.accessor_label = accessor_label
        self.filter = filter
        self.many = many
        self.entity_type = entity_type

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        lst_accessor = self.accessor.split(".")
        lst_accessor_label = self.accessor_label.split(".")
        qs_attr = lst_accessor.pop(0)
        for obj1 in getattr(obj, qs_attr).filter(**self.filter):
            for acc in lst_accessor:
                obj1 = getattr(obj1, acc)
            r1 = {"id": obj1.pk}
            if self.entity_type is not None:
                r1["kind"] = self.entity_type
            else:
                r1["kind"] = obj1.__class__.__name__.lower()
            label = obj1
            for acc in lst_accessor_label:
                label = getattr(label, acc)
            r1["name"] = label
            res.append(r1)
        if len(res) == 0 and self.optional:
            return None
        if self.many:
            return res
        return res[0]


class TsSameAsField(TypesenseField):
    def __init__(
        self,
        type: FieldType,
        domain: Optional[str] = None,
        facet: bool = False,
        optional: bool = False,
        index: bool = True,
        sort: bool = False,
        infix: bool = False,
        locale: Optional[str] = None,
        num_dim: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(
            type, facet, optional, index, sort, infix, locale, num_dim, field_name
        )
        self.domain = domain

    def get_data_representation(self, obj: Model) -> Any:
        filter = {}
        if self.domain is not None:
            filter["uri__contains"] = self.domain
        return list(obj.uri_set.all().exclude(**filter).values_list("uri", flat=True))


class TsReferencesField(TypesenseField):
    @classmethod
    @cache
    def get_zotero_entry(cls, url):
        json = requests.get(
            url, params={"key": os.environ.get("ZOTERO_API_KEY")}
        ).json()
        return json["data"]

    def serialize_ref(self, ref):
        bib = json.loads(ref.bibtex)
        res = {
            "id": ref.pk,
            "folio": None,
            "start_page": None,
            "end_page": None,
            "kind": None,
            "shortTitle": None,
            "title": None,
        }
        if ref.folio is not None:
            if len(ref.folio) > 0:
                res["folio"] = ref.folio
        if ref.pages_start is not None:
            res["start_page"] = ref.pages_start
        if ref.pages_end is not None:
            res["end_page"] = ref.pages_end
        bib = self.get_zotero_entry(ref.bibs_url)
        if "itemType" in bib:
            res["kind"] = bib["itemType"]
        for key in ["shortTitle", "title"]:
            if key in bib:
                res[key] = bib[key]
        tags = bib.get("tags", [])
        tag_group = [tag["tag"][2:] for tag in tags if tag["tag"].startswith("1_")]
        if len(tag_group) == 1:
            res["tag"] = tag_group[0]
        else:
            res["tag"] = "Allgemein"

        return res

    def get_data_representation(self, obj: Model) -> Any:
        refs = Reference.objects.filter(object_id=obj.pk)
        if refs.count() == 0 and self.optional:
            return None
        res = [self.serialize_ref(ref) for ref in refs]
        return res
