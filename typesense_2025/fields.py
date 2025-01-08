from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
from django.db.models import Model

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
        value = getattr(obj, self.field_name)
        return value

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
