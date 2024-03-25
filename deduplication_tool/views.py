from django.shortcuts import render
from django.http import JsonResponse
from dubletten_tool.models import Group, StatusButtonGroup
# Create your views here.


# Get Groups with filter


def get_groups(request, **kwargs):
     if request.method == "GET":
        filter = kwargs.get("val")
        filter = filter.replace("__", " ")
        if filter == "get_all_groups":
            filter = None

        d = json.loads(request.GET.get("data"))
        gender = kwargs.get("gender")
        if gender == "Other":
            gender = [None, "third gender"]
        else: 
            gender = [gender.lower()]
            
        context = {}
        if not filter:
            groups = Group.objects.filter(_gender__in=gender)

        else: 
            groups = Group.objects.filter(name__istartswith=filter, _gender__in=gender)

        groups = list(groups)

        if len(groups) > 100:
            test_groups = set(groups)
            for k, v in d.items():
                if v == "true":
                    val = True
                else: 
                    val = False
                temp = [b.related_instance for b in StatusButtonGroup.objects.filter(kind__id=int(k), value=val)]
                test_groups = test_groups.intersection(set(temp))
            res = [g for g in groups if g in test_groups]
        else:
            res = [g for g in groups if g.check_status(d)]
            res = list(res)

        context["groups"] = res           
        count = len(context["groups"])
        context["group_count"] = count

        html = render_to_string("group_list.html", context, request)

        return JsonResponse({"groups": html, "group_count": count})

# Get Singles with filter


# get one group or one single by id


# get suggestions


# get note


# post note


# merge group


# remerge group
