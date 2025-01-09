from typing import Dict, Any, List
from dataclasses import fields
from django.db.models import QuerySet, Model
from dataclasses import dataclass
from .fields import (
    TypesenseField,
    TsFieldGender,
    TsFieldTimestamp,
    TsStatusField,
    TsFixedStringField,
    TsRelationFlatField,
)


class BaseCollection:
    queryset: QuerySet
    token_separators: List[str]
    symbols_to_index: List[str]
    default_sorting_field: str

    def get_schema(self) -> Dict[str, Any]:
        """
        Automatically generates the schema by iterating through all dataclass fields
        that are instances of TypesenseField
        """
        schema_fields = []

        # Iterate through all dataclass fields
        for field_2 in fields(self):
            field_value = getattr(self, field_2.name)
            if hasattr(field_value, "to_dict"):  # Check if it's a TypesenseField
                schema_fields.append(field_value.to_dict(field_2.name))
        schema = {"name": self.get_collection_name(), "fields": schema_fields}
        if hasattr(self, "token_separators"):
            schema["token_separators"] = self.token_separators
        if hasattr(self, "default_sorting_field"):
            schema["default_sorting_field"] = self.default_sorting_field
        if hasattr(self, "symbols_to_index"):
            schema["symbols_to_index"] = self.symbols_to_index
        return schema

    def get_collection_name(self) -> str:
        """
        Returns the collection name. Override this in subclasses if needed.
        """
        return self.__class__.__name__.lower()

    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Converts Django queryset objects into Typesense documents.
        Each document is a dictionary with field names as keys and their processed values.

        Returns:
            List of dictionaries ready to be indexed in Typesense
        """
        if not hasattr(self, "queryset"):
            raise AttributeError("Collection must have a 'queryset' attribute defined")

        documents = []

        for obj in self.queryset:
            document = self._process_object(obj)
            documents.append(document)

        return documents

    def _process_object(self, obj: Model) -> Dict[str, Any]:
        """
        Process a single Django model instance into a Typesense document

        Args:
            obj: Django model instance

        Returns:
            Dictionary with processed field values
        """
        document = {}

        for field_c in fields(self):
            if hasattr(field_c.default, "get_data_representation"):
                document[field_c.name] = field_c.default.get_data_representation(obj)

        return document


@dataclass
class PersonCollection(BaseCollection):
    id: TypesenseField = TypesenseField(type="int32", field_name="pk")
    name: TypesenseField = TypesenseField(type="string", field_name="name", sort=True)
    firstName: TypesenseField = TypesenseField(
        type="string", field_name="first_name", optional=True
    )
    gender: TsFieldGender = TsFieldGender(
        type="string", facet=True, optional=True, sort=True, field_name="gender"
    )
    startDate: TsFieldTimestamp = TsFieldTimestamp(
        type="int64", sort=True, field_name="start_date"
    )
    endDate: TsFieldTimestamp = TsFieldTimestamp(
        type="int64", sort=True, field_name="end_date"
    )
    startDateWritten: TypesenseField = TypesenseField(
        type="string", optional=True, field_name="start_date_written"
    )
    endDateWritten: TypesenseField = TypesenseField(
        type="string", optional=True, field_name="end_date_written"
    )
    status: TsStatusField = TsStatusField(type="string", facet=True, sort=True)
    kind: TsFixedStringField = TsFixedStringField(type="string", string="person")
    functions: TsRelationFlatField = TsRelationFlatField(
        type="string[]", accessor="personinstitution_set.relation_type.name", facet=True
    )
    institutions: TsRelationFlatField = TsRelationFlatField(
        type="string[]",
        accessor="personinstitution_set.related_institution.name",
        facet=True,
    )

    def get_collection_name(self):
        return "viecpro_v3_person"

    def __init__(
        self,
        queryset: QuerySet,
    ):
        self.queryset = queryset
        self.token_separators = ["-"]
        self.default_sorting_field = "name"
