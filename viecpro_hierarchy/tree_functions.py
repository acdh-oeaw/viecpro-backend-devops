from django.conf import settings


BASE_URI = getattr(settings, "viecpro_hierarchy_BASE_URI", "https://viecpro.acdh-dev.oeaw.ac.at")
#BASE_URI = "https://viecpro.acdh-dev.oeaw.ac.at"
#BASE_URI = "http://127.0.0.1:8000"

def convert_class_name(entity):
    if entity.__class__.__name__ == "PersonInstitutionRelation":
        return "Funktion"
    else:
        return entity.__class__.__name__


def get_meta(entity, rel=None):
    """
    :param entity: expects an entity
    :param rel: if entity is receing end of a relation, store the relation dates within the entity meta
    :return: dictionary of metadata on entity
    """
    res = {}
    res["entity_type"] = convert_class_name(entity)

    if rel:
        res["rel_start"] = str(rel.start_date)
        res["rel_end"] = str(rel.end_date)

    if res["entity_type"] != "Funktion":
        res["start"] = str(entity.start_date)
        res["end"] = str(entity.end_date)
        res["url"] = BASE_URI + entity.get_absolute_url()

    res["label"] = entity.__str__()
    res["pk"] = entity.pk

    return res


def get_new_pk(entity):
    res = convert_class_name(entity) + "_" + str(entity.pk)
    return res



def institution_write_related_insts(entity, direction="down", with_funcs=False, with_person=False, exclude=False):

    if direction == "down":
        insts = entity.get_related_institutionA_instances()
    else:
        insts = entity.get_related_institutionB_instances()

    if not with_funcs and not with_person:

        if exclude:
            res = [institution_write_related_insts(el, direction) for el in insts]
        else:
            res = {"name": get_new_pk(entity), "meta": get_meta(entity),"children": [institution_write_related_insts(el, direction) for el in insts]}

    else:

        res = {"name": get_new_pk(entity), "meta": get_meta(entity), "children":
            [institution_write_related_insts(el, direction, with_funcs=with_funcs, with_person=with_person) for el in
             insts] + inst_write_related_funcs(entity, with_person=with_person)}

    return res


def inst_write_related_funcs(entity, with_person=False):
    rel_types = set(entity.person_relationtype_set.exclude(name="am Hofstaat"))
    res = []
    if with_person:

        for rt in rel_types:
            rels = entity.personinstitution_set.filter(relation_type=rt)
            res.append({"name": get_new_pk(rt), "meta":get_meta(rt), "children":[
                {"name": get_new_pk(r.related_person), "meta": get_meta(r.related_person, r), "children": []}
             for r in rels]})

    else:
        for rt in rel_types:
            res.append({"name": get_new_pk(rt), "meta":get_meta(rt), "children": []})

    return res


def func_write_hierarchy(entity):
    insts = set(entity.institution_set.all())

    res = {"name":get_new_pk(entity), "meta":get_meta(entity), "children": [
        institution_write_related_insts(i, direction="up") for i in insts]}

    return res


def func_write_amt_and_person(entity):
    insts = set(entity.institution_set.all())
    res = {"name": get_new_pk(entity), "meta": get_meta(entity), "children": []}

    for i in insts:
        rels = entity.personinstitution_set.filter(related_institution=i).order_by("related_person__name").distinct()
        temp = {"name":get_new_pk(i), "meta":get_meta(i), "children":[{
            "name":get_new_pk(rel.related_person), "meta":get_meta(rel.related_person, rel), "children":[]}
        for rel in rels]}
        res["children"].append(temp)

    return res


def person_write_related_funcs(entity):
    rel_types  = set(entity.institution_relationtype_set.exclude(name="am Hofstaat"))
    res = {"name": get_new_pk(entity), "meta":get_meta(entity),"children": [] }
    for rt in rel_types:
        rels = entity.personinstitution_set.filter(relation_type=rt)
        res["children"].append({"name": get_new_pk(rt), "meta":get_meta(rt),"children": [
            {"name": get_new_pk(r.related_institution),"meta": get_meta(r.related_institution, r),"children":
        institution_write_related_insts(r.related_institution, direction="up", exclude=True)} for r in rels]})

    return res