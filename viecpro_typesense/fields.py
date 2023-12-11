from viecpro_typesense import Field, O

from .handlers import *


class MainOwnerField(Field):
    class Config:
        options = O(type="object", optional=True, facet=True)
        handler = MainOwnerFieldHandler


class HofstaatsinhaberField(Field):
    class Config:
        options = O(type="object[]", optional=True, facet=True)
        handler = HofstaatsinhaberHandler


class RelatedReferenceDocField(Field):
    class Config:
        handler = ContentTypeDocIDHandler
        options = O(type="object", optional=True)


class TitlesNestedObjectField(Field):
    class Config:
        handler = GenericTitleFieldHandler
        options = O(type="object[]", optional=True)


class LabelsNestedObjectField(Field):
    class Config:
        handler = GenericLabelFieldHandler
        options = O(type="object[]", optional=True)


class TextsNestedObjectField(Field):
    class Config:
        handler = GenericTextFieldHandler
        options = O(type="object[]", index=False, optional=True)


class FunctionsArrayField(Field):
    handler = ParseFunctionsHandler
    options = O(type="object", optional=True)


class SourceField(Field):
    class Config:
        handler = RelatedRelationEntityFieldHandler
        options = O(type="object")


class TargetField(Field):
    class Config:
        handler = RelatedRelationEntityFieldHandler
        options = O(type="object")


class WrittenDateField(Field):
    class Config:
        handler = DateWrittenHandler
        options = O(type="string")


class DateObjectDateField(Field):
    class Config:
        handler = StringHandler
        options = O(type="string")


class FullNameField(Field):
    class Config:
        handler = FullNameHandler
        options = O(type="string")


class StringField(Field):
    class Config:
        handler = StringHandler
        options = O(type="string", optional=True)


class ObjectIDField(Field):
    class Config:
        handler = IntHandler
        options = O(type="int64")


class KindField(Field):
    class Config:
        handler = KindHandler
        options = O(type="string")


class RelatedIDField(Field):
    class Config:
        handler = RelatedIDHandler
        options = O(type="string")
