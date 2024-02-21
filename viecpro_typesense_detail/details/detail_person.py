from .utils import F, C, format_and_orient_relation, to_rel
from apis_core.apis_entities.models import Person
from apis_core.apis_relations.models import PersonInstitution
from typing import List, Dict, Any
from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import VocabsBaseClass
from apis_core.apis_relations.models import PersonPerson, PlacePlace, EventEvent, WorkWork, InstitutionInstitution


# maps certain occurrences of label_types to keys in the result dictionary
perper_map = {
    'Berufliche Beziehung >> Tätigkeiten für ausländische Höfe': "non_court_functions",
    'Berufliche Beziehung': "person_relations_court",
    'Doubletten Beziehung': "duplicates",
    'Verwandtschaftliche Beziehung': "marriages_and_family_relations",
    'Kirchl. Amtsbeziehung': "relations_to_church_and_orders",
    'Dynastische Beziehung': "non_court_functions"
}

# all fields of the person_detail collection
person_fields = [
    # if no type given, default is "object[]" which is the typesense signature for an array of objects
    F("id", type="string", index=True, optional=False),
    F("model", type="string", index=True, optional=False),
    F("object_id", type="string", index=True, optional=False),
    F("had_courts"),
    F("place_of_birth", type="object"),
    F("place_of_death", type="object"),
    F("confession", type="string[]"),
    # F("collected_titles"),
    F("first_marriage", type="string"),
    F("married_names"),
    F("duplicates"),
    F("alternative_first_names", type="string[]"),
    F("alternative_last_names", type="string[]"),
    F("alternative_birth_dates", type="string[]"),
    F("alternative_death_dates", type="string[]"),
    F("honorary_titles"),
    F("academic_titles"),
    F("sources"),  # referencesData (shortTitle, folio (as link if containts https))
    F("court_functions"),  # relData.PersonInstitution
    F("person_relations_court"),  # Berufliche Beziehung PerPer
    F("other_relations_court"),  # labelData Court Other
    # Verwandtschatfliche Beziehung PerPer
    F("marriages_and_family_relations"),
    # label_data and RelData Kirchliche Amtsbeziehung
    F("relations_to_church_and_orders"),
    F("non_court_functions")  # labelData other jobs
]

# unused atm, we only build the person collection (for now)
collections = [f"viecpro_{model}_detail" for model in [
    "person", "institution", "place", "work", "source", "court"]]

person_schema = {
    "name": "viecpro_person_detail",
    "enable_nested_fields": True,
    "fields": [
        f.to_dict() for f in person_fields
    ]
}


# def to_rel(l):
#     """
#     Helper that maps a label to a kind of relation-like datastructure. 
#     Note that the name of the fields are changed.
#     """
#     return {"name": l.label, "start_date": l.start_date_written or "", "end_date": l.end_date_written or ""}


def parse_person_labels(p, res:Dict[str, Any]):
    """
    Parses all person labels by matching against exact label-types.
    Takes, appends to and returns the result-dict.
    """
    l: Label
    for l in p.label_set.all().prefetch_related("label_type"): # type: ignore
        match l.label_type.name:  # type: ignore
            case "alternativer Vorname" | "Schreibvariante Vorname":
                res["alternative_first_names"].append(l.label)  # type: ignore
            case "alternativer Nachname" | "Schreibvariante Nachname":
                res["alternative_last_names"].append(l.label)  # type: ignore
            case "alternatives Sterbedatum":
                res["alternative_death_dates"].append(l.label)  # type: ignore 
            case "alernatives Geburtsdatum":
                res["alternative_birth_dates"].append(l.label)  # type: ignore
            case "Konfession":
                res["confession"].append(l.label)  # type: ignore
            case "Adelstitel / -prädikat" | "Auszeichnung" | "Stand":
                res["honorary_titles"].append(to_rel(l))
            case "Schreibvariante Nachname verheiratet" | "Schreibvariante Nachname verheiratet (2. Ehe)":
                res["married_names"].append(to_rel(l))
            case 'Nachname verheiratet (1. Ehe)':
                res["first_marriage"] = l.label  # type: ignore
            case "Sonstiger Hofbezug":
                res["other_relations_court"].append(to_rel(l))
            case "Akadem. Titel":
                res["academic_titles"].append(to_rel(l))
            case "Funktion, Amtsinhabe und Beruf":
                res["non_court_functions"].append(to_rel(l))
            case "Kirche" | "Orden":
                res["relations_to_church_and_orders"].append(to_rel(l))
    return res


# def format_and_orient_relation(rel: AbstractRelation, reverse=False):
#     """
#     Returns a nested structure that represents a relation. Maps keys and re-orients the relation
#     if the reverse flag is set.

#     Background:
#     Relations are oriented from entity a to b. In the ui, they are shown always from the 
#     view of the selected entity, i.e. with the selected entity in A-position (subject if you will).
#     So if a relation has the selected entity in target position, it gets reversed here.
#     """
#     if reverse:
#         target_entity = getattr(rel, rel.get_related_entity_field_nameA())
#         relation_type = rel.relation_type.name_reverse
#     else:
#         target_entity = getattr(rel, rel.get_related_entity_field_nameB())
#         relation_type = rel.relation_type.name
#     target = {
#         "name": str(target_entity),
#         "object_id": str(target_entity.id),
#         "model": str(target_entity.__class__.__name__)}

#     return {"relation_type": relation_type, "target": target, "start_date": rel.start_date_written or "", "end_date": rel.end_date_written or ""}


def check_person_relation_type(rel:PersonInstitution):
    """
    Helper that returns the first match from  list of parts of label-types that
    are present in a relation.

    Returns False if no match is found.
    """
    hierarchy = str(VocabsBaseClass.objects.get(id=rel.relation_type.id)) # type: ignore
    checklist = [
        'Berufliche Beziehung >> Tätigkeiten für ausländische Höfe',
        'Berufliche Beziehung',
        'Doubletten Beziehung',
        'Verwandtschaftliche Beziehung',
        'Kirchl. Amtsbeziehung',
        'Dynastische Beziehung',
    ]

    for check in checklist:
        if check in hierarchy:
            return check

    return False


def parse_person_relations(p:Person, res:Dict[str, Any])-> Dict[str, Any]:
    rel: Any
    temp_rel: Any
    for rel in p.get_related_relation_instances():
        model_name: Any= rel.__class__.__name__

        # handle orientation of relation and format relation to target format
        if rel.get_related_entity_instanceB() == p:
            temp_rel = format_and_orient_relation(rel, reverse=True)
        else:
            temp_rel = format_and_orient_relation(rel)

        if model_name == "PersonPerson":
            check = check_person_relation_type(rel)
            if check:
                res[perper_map[check]].append(temp_rel)

        if model_name == "PersonInstitution":
            res["court_functions"].append(temp_rel)

        if rel.relation_type.name == "ist geboren in":
            res["place_of_birth"] = temp_rel["target"]

        if rel.relation_type.name == "ist gestorben in":
            res["place_of_death"] = temp_rel["target"]

        if rel.relation_type.name == "hatte den Hofstaat":
            res["had_courts"].append(temp_rel["target"])

        # put relation in right bucket

    return res


def main(offset:int=0):

    # instanciate the collection and create the schema from it
    c = C(name="viecpro_detail_person", fields=person_fields)
    schema = c.to_schema()


    results: List[Any] = []
    model = Person
    data = model.objects.all().prefetch_related(*[f"{m._meta.model_name}_set" for m in model.get_related_relation_classes( # type: ignore
    ) if m not in [PersonPerson, PlacePlace, EventEvent, WorkWork, InstitutionInstitution]])
    count = len(data)

    for idx, instance in enumerate(data):
        if idx < offset:
            continue

        if idx % 1000 == 0:
            print(f"{idx}/{count}")

        res = c.to_empty_result_dict()
        res = parse_person_labels(instance, res)
        res = parse_person_relations(instance, res)
        res["id"] = f"detail_{model._meta.model_name}_{instance.id}" # type: ignore
        res["object_id"] = str(instance.id) # type: ignore
        res["model"] = model.__name__
        results.append(res)

    return {"schema": schema, "results": results}
