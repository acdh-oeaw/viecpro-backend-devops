from apis_core.apis_vocabularies.models import VocabsBaseClass
from viecpro_typesense.classes import Handler
import json
import django
import re
from collections import defaultdict
from apis_core.apis_relations.models import PersonInstitution

django.setup()

REG_SKL = re.compile(r"\<.*?\>")
REG_EKL = re.compile(r"\[.*?\]")
REG_GKL = re.compile(r"\{.*?\}")

OwnerLookup = defaultdict(list)

[OwnerLookup[el.related_institution.id].append({
    "name": f"{str(el.related_person)} (*{el.related_person.start_date.year})", "relation_type": el.relation_type.name_reverse, "object_id": el.related_person.id, "model": "Person",
    "start_date": el.start_date_written.split("<")[0] if el.start_date_written else "",
            "end_date": el.end_date_written.split("<")[0] if el.end_date_written else "", }) for el in PersonInstitution.objects.filter(relation_type__name="hatte den Hofstaat")]


def fixstring(string):
    string = str(string)
    string = re.sub(REG_SKL, "", string)
    string = re.sub(REG_EKL, "", string)
    string = re.sub(REG_GKL, "", string)
    return string


class ErrorCount:
    reference_doc = 0


class StringHandler(Handler):
    def func(x): return fixstring(x) if x else ""


RelatedIDHandler = StringHandler


class IntHandler(Handler):
    def func(x): return int(x) if x else None


class KindHandler(Handler):
    def func(x): return str(x.name) if x and x.name else ""


# class RelatedIDHandler(Handler):
#     def func(x): return str(x.id)


class FullNameHandler(Handler):
    def func(x, y): return f"{fixstring(x)}, {fixstring(y)}"


class DateWrittenHandler(Handler):
    def func(x): return x.split("<")[0] if x else ""


class RelatedRelationEntityFieldHandler(Handler):
    def func(x): return {
        "name": str(x),
        "object_id": str(x.id),
        "model": str(x.__class__.__name__),
    }


class GenericLabelFieldHandler(Handler):
    def func(x): return [
        {
            "name": l.label,
            "object_id": str(l.id),
            "label_type": l.label_type.name,
            "start_date": l.start_date_written.split("<")[0] if l.start_date_written else "",
            "end_date": l.end_date_written.split("<")[0] if l.end_date_written else "",
            "label_hierarchy": str(VocabsBaseClass.objects.get(id=l.label_type.id)),
            "model": "Label",
        }
        for l in x.label_set.all()
    ]


class GenericTitleFieldHandler(Handler):
    def func(x): return [
        {"name": t.name, "object_id": str(t.id), "model": "Title"}
        for t in x.title.all()
    ]


class GenericTextFieldHandler(Handler):
    def func(x): return [
        {"text": t.text, "kind": t.kind.name,
            "object_id": str(t.id), "model": "Text"}
        for t in x.text.all()
    ]


class ParseFunctionsHandler(Handler):
    def func(x): return [f.name for f in x.institution_relationtype_set.all()]


class ParsePersonInstitutionHandler(Handler):
    def func(x): return [f.related_institution.name for f in x.personinstitution_set.all()]


class GenericDocIDHandler(Handler):
    def func(x): return f"{x.__class__.__name__}_{x.id}"


class ContentTypeDocIDHandler(Handler):

    def func(ct, obj_id):
        # print(ct, type(ct), obj_id, type(obj_id))
        model = ct.model_class()
        model_name = model.__name__
        try:
            related_name = model.objects.get(id=obj_id)
        except Exception as e:
            print("object did not exis")
            ErrorCount.reference_doc += 1
            related_name = "Not Found"

        return {
            "id": f"{model_name}_{obj_id}",
            "object_id": f"{obj_id}",
            "model": model_name,
            "name": str(related_name)
        }


class BibtexTitleHandler(Handler):
    def func(bibtex):
        bib = json.loads(bibtex)
        return bib.get("shortTitle", "")


class BibtexShortTitleHandler(Handler):
    def func(bibtex):
        bib = json.loads(bibtex)
        return bib.get("title", "")


class BibtexTypeHandler(Handler):
    def func(bibtex):
        bib = json.loads(bibtex)
        return bib.get("type", "")


class HofstaatsinhaberHandler(Handler):

    def func(x):
        return OwnerLookup.get(x.id, [])


class MainOwnerFieldHandler(Handler):

    def func(x):
        res = OwnerLookup.get(x.id, [])
        if res:
            return res[0]
        else:
            return {}


class RelationTypeHierarchyHandler(Handler):
    def func(x): return f"{VocabsBaseClass.objects.get(id=x.id)}" if x else ""
