from .handlers import GenericDocIDHandler
from viecpro_typesense import Collection, StaticField, CollectionConfig, O, Field
from copy import deepcopy
from .fields import StringField, FullNameField, TitlesNestedObjectField, RelationTypeHierarchyHandler, WrittenDateField, BibtexShortTitleHandler, BibtexTitleHandler, BibtexTypeHandler, RelatedReferenceDocField, ObjectIDField, DateObjectDateField, LabelsNestedObjectField, KindField, SourceField, TargetField, HofstaatsinhaberField, MainOwnerField, FunctionsArrayField, PersonInstitutionArrayField
from apis_bibsonomy.models import Reference
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_entities.models import AbstractEntity, Institution, Person, Place, Event, Work


class ReferenceCollection(Collection):
    class Config:
        name = "references"
        nested = True
        model = Reference
        queryset = Reference.objects.all

    id = StringField("id", handler=GenericDocIDHandler, pass_instance=True)
    start_page = StringField("pages_start", options=O(optional=True))
    end_page = StringField("pages_end", options=O(optional=True))
    folio = StringField("folio", options=O(optional=True))
    model = StaticField(value="Reference")
    # bibtex = StringField("bibtex", handler=lambda x: json.loads(x), options=O(type="object", optional=True))
    title = StringField("bibtex", handler=BibtexTitleHandler,
                        options=O(type="string", optional=True))
    shortTitle = StringField(
        "bibtex", handler=BibtexShortTitleHandler, options=O(facet=True, optional=True))
    kind = StringField("bibtex", handler=BibtexTypeHandler,
                       options=O(facet=True, optional=True))
    related_doc = RelatedReferenceDocField(
        ("content_type", "object_id"), options=O(facet=True, optional=True))


def collection_factory(name, fields, config):
    fields.update({"Config": config})
    cls = type(name, (Collection,), fields)
    return cls


def shared_fields(m): return {
    "id": StringField("id", handler=GenericDocIDHandler, pass_instance=True),
    "object_id": ObjectIDField("id"),
    "start_date": WrittenDateField("start_date_written"),
    "end_date": WrittenDateField("end_date_written"),
    "start": DateObjectDateField("start_date"),
    "end": DateObjectDateField("end_date"),
    "model": StaticField(value=m.__name__, options=O(facet=False)),
}

def ampelhandler(x):
    if hasattr(x, "ampel"):
        return x.ampel.status
    return ""

def get_entity_specific_detail_fields(entity):
    fields = {}
    match entity:
        case "person":
            pass
        case "institution":
            pass
        case "place":
            pass
        case "event":
            pass
        case "work":
            pass
        case _:
            raise Exception(
                f"Can't find entity {entity} in 'get_entity_specific_detail_fields'")

    return fields


def genderhandler(x):
    match getattr(x, "gender", None):
        case "male": return "männlich"
        case "female": return "weiblich"
        case _: return "unbekannt"


def labelhandler(x):
    label_types = ["Bezeichnung, alternativ", "Nachname verheiratet", "Nachname verheiratet (1. Ehe)", "Nachname verheiratet (2. Ehe)", "Nachname verheiratet (3. Ehe)", "Schreibvariante Nachname", "Schreibvariante Nachname verheiratet", "Schreibvariante Nachname verheiratet (1. Ehe)", "Schreibvariante Nachname verheiratet (2. Ehe)", "Schreibvariante Vorname"]
    labels = x.label_set.all()
    return [label.label for label in labels if label.label_type in label_types]


def create_entity_collections():
    res = []
    for m in AbstractEntity.get_all_entity_classes():
        if m is not Work:
            config = CollectionConfig()
            config.model = m
            config.name = m.__name__.lower()+"s"
            config.queryset = lambda m=m: m.objects.all(
            ) if m is not Institution else m.objects.exclude(kind__name="Hofstaat")
            config.nested = True

            base_fields = deepcopy(shared_fields(m))
            base_fields.update({"name": StringField("name", options=O(
                facet=False)), "labels": LabelsNestedObjectField("id", pass_instance=True)})

            if m is not Person:
                base_fields.update(
                    {"kind": KindField("kind", options=O(facet=True))})

                if m is Place:
                    base_fields.update(
                        {
                            "lat": StringField("lat"),
                            "long": StringField("lng"),
                        }
                    )
            else:
                per_fields = {
                    "first_name": StringField("first_name", options=O(sort=True)),
                    "fullname": FullNameField(("name", "first_name"), options=O(sort=True)),
                    "gender": StringField("gender", pass_instance=True, handler=genderhandler, options=O(facet=True, optional=True, type="string")),
                    "titles": TitlesNestedObjectField("id", pass_instance=True),
                    "functions": FunctionsArrayField("id", pass_instance=True, options=O(facet=True)),# TODO: need to remove need to pass field param to field with pass_instance. id won't be accessed here, its a dummy
                    "institutions": PersonInstitutionArrayField("id", pass_instance=True, options=O(facet=True)),
                }
                base_fields.update(per_fields)
            detail_fields = get_entity_specific_detail_fields(
                m.__name__.lower())
            base_fields["ampel"] = StringField("ampel", pass_instance=True, options=O(facet=True), handler=ampelhandler)
            base_fields["alternativenames"] = Field("alternativenames", pass_instance=True, handler=labelhandler, options=O(facet=True, type="string[]", optional=True))
            base_fields.update(detail_fields)

            cls = collection_factory(
                f"{m.__name__}Collection", base_fields, config)
            res.append(cls)
    return res


def create_relation_collections():
    res = []
    for m in AbstractRelation.get_all_relation_classes():
        if m.objects.all().count() > 0 and not "Work" in m.__name__:
            config = CollectionConfig()
            config.model = m
            config.name = m.__name__
            config.queryset = lambda m=m: m.objects.exclude(
                relation_type__name__in=["data merged from",])
            config.nested = True

            base_fields = deepcopy(shared_fields(m))

            base_fields.update(
                {
                    "source": SourceField(m.get_related_entity_field_nameA()),
                    "source_kind": StaticField(
                        m.get_related_entity_classA().__name__, options=O(facet=True)
                    ),
                    "target": TargetField(m.get_related_entity_field_nameB()),
                    "target_kind": StaticField(
                        m.get_related_entity_classB().__name__, options=O(facet=True)
                    ),
                    "relation_type_id": StringField("relation_type", options=O(type="int64"), handler=lambda x: x.id),
                    "relation_type": KindField("relation_type", options=O(facet=True)),
                    "relation_type_hierarchy": StringField("relation_type", options=O(optional=True, type="string"), handler=RelationTypeHierarchyHandler),
                    "relation_reverse": StringField("id", handler=lambda x: str(x.relation_type.name_reverse), options=O(optional=True), pass_instance=True)
                }
            )
            cls = collection_factory(
                f"{m.__name__}Collection", base_fields, config)
            res.append(cls)
        else:
            print("was false for: ", m.__name__)

    return res


class HofstaatCollection(Collection):
    class Config:
        name = "courts"
        model = Institution
        def queryset(): return Institution.objects.filter(kind__name="Hofstaat")
        nested = True

    id = StringField(
        "id",  handler=lambda x: f"Hofstaat_{x.id}", pass_instance=True)
    name = StringField("name", options=O(facet=True, sort=True))
    owner = HofstaatsinhaberField("id", pass_instance=True)
    main_owner = MainOwnerField("id", pass_instance=True)
    object_id = ObjectIDField("id")
    start_date = WrittenDateField("start_date_written")
    end_date = WrittenDateField("end_date_written")
    start = DateObjectDateField("start_date")
    end = DateObjectDateField("end_date")
    # Maybe need to change model to hofstaat here
    model = StaticField(value="Hofstaat", options=O(facet=True))
    kind = KindField("kind", options=O(facet=True))
    labels = LabelsNestedObjectField("id", pass_instance=True)


def unified_fields(m): return {
    "id": StringField("id", handler=GenericDocIDHandler, pass_instance=True),
    "object_id": ObjectIDField("id"),
    "name": StringField("name", options=O(sort=True)),
    "start_date": WrittenDateField("start_date_written", options=O(optional=True)),
    "end_date": WrittenDateField("end_date_written", options=O(optional=True)),
    "start": DateObjectDateField("start_date", options=O(optional=True)),
    "end": DateObjectDateField("end_date", options=O(optional=True)),
    "model": StaticField(value=m.__name__, options=O(facet=True)),
    "kind": KindField
}


def create_unified_collections():
    pass
    # TODO: decide on which models to include and write the logic.
    # res = []
    # for m in AbstractEntity.get_all_entity_classes():
    #         config = CollectionConfig()
    #         config.model = m
    #         config.name = m.__name__.lower()+"s"
    #         config.queryset = lambda m=m: m.objects.all() if m is not Institution else m.objects.exclude(kind__name="Hofstaat")
    #         config.nested = True

    #         base_fields = deepcopy(shared_fields(m))
    #         base_fields.update({"name": StringField("name", options=O(facet=True)), "labels": LabelsNestedObjectField("id", pass_instance=True)})

    #         if m is not Person:
    #             base_fields.update({"kind": KindField("kind", options=O(facet=True))})

    #             if m is Place:
    #                 base_fields.update(
    #                     {
    #                         "lat": StringField("lat"),
    #                         "long": StringField("lng"),
    #                     }
    #                 )
    #         else:
    #             per_fields = {
    #                 "first_name": StringField("first_name"),
    #                 "fullname": FullNameField(("name", "first_name")),
    #                 "gender": StringField("gender", options=O(facet=True, optional=True, type="string")),
    #                 "titles": TitlesNestedObjectField("id", pass_instance=True),
    #                 # "functions": FunctionsArrayField("id", pass_instance=True),# TODO: need to remove need to pass field param to field with pass_instance. id won't be accessed here, its a dummy
    #             }
    #             base_fields.update(per_fields)

    #         cls = collection_factory(f"{m.__name__}Collection", base_fields, config)
    #         res.append(cls)
    #     return res
