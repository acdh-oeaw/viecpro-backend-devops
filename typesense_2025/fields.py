from dataclasses import dataclass
from os import wait
from typing import List, Optional, Literal, Dict, Any, Tuple
from django.db.models import Model
import re
import datetime
from django.contrib.contenttypes.models import ContentType
from functools import cache


def clean_text(text):
    text = str(text)
    # Remove content within brackets and the brackets themselves
    text = re.sub(r"<[^>]+>", "", text)  # Remove <...>
    text = re.sub(r"\[[^\]]+\]", "", text)  # Remove [...]
    text = re.sub(r"\{[^\}]+\}", "", text)  # Remove {...}
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
    r1["startDateWritten"] = clean_text(obj.start_date_written)
    r1["endDateWritten"] = clean_text(obj.end_date_written)
    return r1


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

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        lst_accessor = self.accessor.split(".")
        qs_attr = lst_accessor.pop(0)
        for obj1 in getattr(obj, qs_attr).filter(**self.filter):
            for acc in lst_accessor:
                obj1 = getattr(obj1, acc)
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
        relations: Optional[List[Tuple]] = None,
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
        if "A" in c or "B" in c:
            mdl = "PersonPersonRelation".lower()
        else:
            mdl = c.replace("_set", "")
        ct = ContentType.objects.get(app_label="apis_vocabularies", model=mdl)
        mc = ct.model_class()
        t1 = mc.objects.get(name=term)
        res.append(t1)
        pc = mc.objects.filter(parent_class_id=t1.pk)
        while pc.count() > 0:
            pc = mc.objects.filter(parent_class__in=pc)
            res.extend([p1 for p1 in pc])
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
            for filter, acc, acc_label, entity_type, rel_types in self.relations:
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
                for obj2 in getattr(obj, qs_attr).filter(**filter):
                    obj1 = obj2
                    for acc in lst_accessor:
                        obj1 = getattr(obj1, acc)
                    r1 = {"id": obj1.pk}
                    if entity_type is not None:
                        r1["kind"] = entity_type
                    else:
                        r1["kind"] = obj1.__class__.__name__.lower()
                    label = obj1
                    if acc_label is not None:
                        for acc in lst_accessor_label:
                            label = getattr(label, acc)
                    r1["name"] = clean_text(str(label))
                    r2 = {"relationType": obj2.relation_type.name, "target": r1}
                    time_data = create_timestamps(obj1)
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
