from typing import Dict, Any, List, Iterable
from dataclasses import fields, field
from django.db.models import QuerySet, Model
from dataclasses import dataclass
from .fields import TypesenseField


class BaseCollection:
    queryset: QuerySet

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

        return {"name": self.get_collection_name(), "fields": schema_fields}

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
    name: TypesenseField = TypesenseField(type="string", facet=True, field_name="name")

    def __init__(self, queryset: QuerySet):
        self.queryset = queryset
