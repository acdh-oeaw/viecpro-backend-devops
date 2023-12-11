from dataclasses import dataclass, asdict, field
from typing import List


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

    def to_empty_result_dict(self):
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
