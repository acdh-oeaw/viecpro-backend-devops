from django.http import JsonResponse
from apis_core.apis_entities.models import Institution, Person
from apis_core.apis_vocabularies.models import PersonInstitutionRelation
import json
from viecpro_hierarchy.tree_functions import *



def method_dispatcher(request, **kwargs):
    """
    pattern = /entity_type/pk/graph_option/direction

    :param request:
    :param kwargs:
    :return:
    """
    entity_type = kwargs.get("entity_type", None)
    pk = kwargs.get("pk", None)
    graph = kwargs.get("graph_option", None)
    direction = kwargs.get("direction", "down")
    if direction == "direction":
        direction = "down"

    pk = int(pk)

    if entity_type == "Person":
        p = Person.objects.get(pk=pk)
        data = person_write_related_funcs(p)

    elif entity_type == "Funktion":
        rt = PersonInstitutionRelation.objects.get(pk=pk)

        if graph == "show amt and persons":
            data = func_write_amt_and_person(rt)
        else:
            data = func_write_hierarchy(rt)

    elif entity_type == "Institution":
        i = Institution.objects.get(pk=pk)

        if graph == "add functions":
            data = institution_write_related_insts(i, with_funcs=True, direction=direction)

        elif graph == "add functions and persons":
            data = institution_write_related_insts(i, with_person=True, direction=direction)

        else:
            data = institution_write_related_insts(i, direction=direction)

    graph_type = graph
    data = {"tree_data":data, "graph_type":graph_type}
    #data = json.dumps(data)


    return JsonResponse(data)
