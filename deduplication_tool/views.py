from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from dubletten_tool.models import Group, StatusButtonGroup, PersonProxy
import json
from deduplication_tool.validation import SelectionState, get_selection_state_from_dict
from pydantic import ValidationError

@method_decorator(login_required, name="dispatch")
class EditorView(TemplateView):
    template_name="deduplication_tool/tool_page.html"

@method_decorator(login_required, name="dispatch")
class ActionHandler(View):
    
    def post(self, request, action, **kwargs):
        data = json.loads(request.body)
        try: 
            selectionState = get_selection_state_from_dict(data)
        except ValidationError as ve: 
            print(ve)
            return JsonResponse({"error": str(ve)})
        
        print(selectionState)
        groups =  data.get("groups").keys()

        # validate all data before running any action
        for g in groups: 
            assert Group.objects.filter(pk=g).exists()
            for member in data["groups"][g]:
                assert PersonProxy.objects.filter(person__id=member).exists()
                assert PersonProxy.objects.get(person__id=member).status == "candidate"

        for s in data["singles"]:
            assert PersonProxy.objects.filter(person__id=s).exists()
            assert PersonProxy.objects.get(person__id=s).status == "single"

        # switch on the action and dispatch right celery task
        

        # return the task id
        return JsonResponse({"action": action, "data": data})
        