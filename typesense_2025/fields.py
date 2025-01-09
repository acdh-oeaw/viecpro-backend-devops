from dataclasses import dataclass
from typing import List, Optional, Literal, Dict, Any, Tuple
from django.db.models import Model
import re
import datetime

# Valid Typesense field types
FieldType = Literal[
    "string",
    "int32",
    "int64",
    "float",
    "bool",
    "geopoint",
    "string[]",
    "int32[]",
    "int64[]",
    "float[]",
    "bool[]",
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

        text = str(value)
        # Remove content within brackets and the brackets themselves
        text = re.sub(r"<[^>]+>", "", text)  # Remove <...>
        text = re.sub(r"\[[^\]]+\]", "", text)  # Remove [...]
        text = re.sub(r"\{[^\}]+\}", "", text)  # Remove {...}
        return text.strip()

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


def camel_case_to_snake(string):
    field_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    field_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", field_name).lower()
    return field_name


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

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        lst_accessor = self.accessor.split(".")
        qs_attr = lst_accessor.pop(0)
        for obj1 in getattr(obj, qs_attr).filter(**self.filter):
            for acc in lst_accessor:
                obj1 = getattr(obj1, acc)
            res.append(obj1)
        return res


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

    def get_data_representation(self, obj: Model) -> Any:
        res = []
        if self.labels is not None:
            for label in obj.label_set.filter(label_type__name__in=self.labels):
                r1 = {"relationType": label.label}
                if label.start_date is not None:
                    start_date = int(label.start_date.strftime("%s"))
                else:
                    start_date = int(datetime.datetime(5000, 1, 1, 0, 0).timestamp())
                if label.end_date is not None:
                    end_date = int(label.end_date.strftime("%s"))
                else:
                    end_date = int(datetime.datetime(5000, 1, 1, 0, 0).timestamp())
                r1["startDate"] = start_date
                r1["endDate"] = end_date
                r1["startDateWritten"] = label.start_date_written
                r1["endDateWritten"] = label.end_date_written
                res.append(r1)
        return res
