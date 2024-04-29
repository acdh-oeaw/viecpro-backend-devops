from django.utils.decorators import method_decorator
from django.http import HttpRequest, JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from dubletten_tool.models import Group, PersonProxy
import json
from enum import StrEnum
from copy import deepcopy
from deduplication_tool.validation.datastructures import *
from typing import Any


class Action(StrEnum):
    REMOVE_SELECTED_MEMBERS = "remove_selected_members"
    MERGE_SELECTED_MEMBERS = "merge_selected_members"
    REMERGE_GROUP = "remerge_group"
    MERGE_ALL_DISPLAYED = "merge_all_displayed"
    GROUP_SELECTED = "group_selected"
    DISSOLVE_GROUP = "dissolve_group"
    CREATE_GROUP_FROM_SINGLE = "create_group_from_single"


@method_decorator(login_required, name="dispatch")
class EditorView(TemplateView):
    template_name = "deduplication_tool/tool_page.html"


@method_decorator(login_required, name="dispatch")
class ActionHandler(View):
    def setup(
        self, request: HttpRequest, *args: list[Any], **kwargs: dict[str, Any]
    ) -> None:
        self.available_actions = Action

        return super().setup(request, *args, **kwargs)

    def dispatch_remove_selected_members(self, raw_data: ActionDataRemoveMember):
        pass

    def dispatch_dissolve_group(self, raw_data: ActionDataDissolveGroup):
        pass

    def dispatch_remerge_group(self, raw_data: ActionDataRemergeGroup):
        pass

    def dispatch_merge_all_displayed(self, raw_data: ActionDataMergeAll):
        pass

    def dispatch_group_selected(self, raw_data: ActionDataGroupSelected):
        pass

    def dispatch_merge_selected_members(self, raw_data: ActionDataMergeSelectedMembers):
        pass

    def dispatch_create_group_from_single(
        self, raw_data: ActionDataCreateGroupFromSingle
    ):
        pass

    def post(self, request: HttpRequest, action: Action, **kwargs: dict[str, Any]):
        data = json.loads(request.body)
        target_group = deepcopy(data.get("target_group", None))
        del data["target_group"]
        print("data after deleting target group", data)

        # raw_state = RawSelectionState(**data)
        # print("raw_state", raw_state)

        print(target_group)

        if action not in [a.value for a in Action]:
            return JsonResponse(
                {
                    "error": f"Action: {action} is not known. Available actions are: {[a.value for a in Action]}"
                }
            )
        if action in [
            Action.REMOVE_SELECTED_MEMBERS,
            Action.REMERGE_GROUP,
            Action.MERGE_SELECTED_MEMBERS,
            Action.DISSOLVE_GROUP,
        ]:
            if not target_group:
                return JsonResponse(
                    {
                        "error": f"Action: {action} depends on a target group. None given."
                    }
                )
        # try:
        #     selectionState = get_selection_state_from_dict(raw_state)
        # except ValidationError as ve:
        #     print(ve)
        #     return JsonResponse({"error": str(ve)})

        # print(selectionState)
        groups = data.get("groups").keys()

        # validate all data before running any action
        for g in groups:
            assert Group.objects.filter(pk=g).exists()
            for member in data["groups"][g]:
                assert PersonProxy.objects.filter(person__id=member).exists()
                assert PersonProxy.objects.get(person__id=member).status == "candidate"

        for s in data["singles"]:
            assert PersonProxy.objects.filter(person__id=s).exists()
            assert PersonProxy.objects.get(person__id=s).status == "single"

        actions = self.available_actions

        match action:
            case actions.DISSOLVE_GROUP:
                self.dispatch_dissolve_group(raw_data=ActionDataDissolveGroup(**data))

            case actions.REMERGE_GROUP:
                self.dispatch_remerge_group(raw_data=ActionDataRemergeGroup(**data))

            case actions.REMOVE_SELECTED_MEMBERS:
                self.dispatch_remove_selected_members(
                    raw_data=ActionDataRemoveMember(**data)
                )

            case actions.GROUP_SELECTED:
                self.dispatch_group_selected(raw_data=ActionDataGroupSelected(**data))

            case actions.MERGE_ALL_DISPLAYED:
                self.dispatch_merge_all_displayed(raw_data=ActionDataMergeAll(**data))

            case actions.MERGE_SELECTED_MEMBERS:
                self.dispatch_merge_selected_members(
                    raw_data=ActionDataMergeSelectedMembers(**data)
                )

            case actions.CREATE_GROUP_FROM_SINGLE:
                self.dispatch_create_group_from_single(
                    raw_data=ActionDataCreateGroupFromSingle(**data)
                )
            case _:
                return JsonResponse(
                    {
                        "error": f"Action: {action} is not known. Available actions are: {[a.value for a in Action]}"
                    }
                )

        # switch on the action and dispatch right celery task

        # return the task id
        return JsonResponse({"action": action, "data": data})
