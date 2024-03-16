from celery import shared_task
from dubletten_tool.src.functions.remerge_single_group import remerge_single_group
from celery.utils.log import get_task_logger
from dubletten_tool.models import Group, StatusButtonGroup, StatusButtonGroupType, PersonProxy
from apis_core.apis_entities.models import Person
from django.http import HttpResponse, JsonResponse
from time import sleep

logger = get_task_logger(__name__)


@shared_task
def remerge_group_task(g_id, vorfin_list=[], groups_to_delete=None):
    """
    Task remerges existing group and creates a new vorfin. Should only be called for groups that already have a vorfin.
    # TODO: needs update, this is also called when there was no vorfin?
    """

    logger.info(f"{g_id=}, {vorfin_list=}, {groups_to_delete=}")
    sleep(2)
    #vorfin_list = []
    # TODO: consider adding check here or in calling view, if group really had a vorfin before.
    if vorfin_list:
        try:
            vorfin_list = [Person.objects.get(id=v.id) for v in vorfin_list]
            logger.info(f"fixed type error, so vorfin list should not be printed below this line.")
        except TypeError as te:
            logger.info(f"caught TypeError and handled it: \n{te}")
            logger.info(f"Vorfin list was true, objects are {vorfin_list}")

    if groups_to_delete:
        if vorfin_list:
            raise Exception(
                f"Assertion error, groups_to_delete was not none, but vorfin_list given. Script does not reflect this Option!")
        for g in groups_to_delete:
            try:
                g = Group.objects.get(id=g)
                vorf = g.vorfin
                vorfin_list.append(vorf)
                logger.info(
                    f"{g=}, {vorf=}, {vorf.id=} Appended vorf to vorfin_list")
            except Exception as e:
                logger.info(
                    f"Error {e}, :: could not get vorfin of group {g=}")

    group = Group.objects.get(id=g_id)
    logger.info("called celery task")
    empty_result = "<p class='text-center'>Nothing to Display.</p>"
    # Single group logic

    # wrap all in exception block and return rerror if anything goes wrong.
    vorfin = group.vorfin
    if vorfin:
        old_vorfin_name = group.vorfin.name
        old_vorfin_id = group.vorfin.id
    else:
        old_vorfin_name = None
        old_vorfin_id = None

    try:
        # TODO: bughunt issue 2: why is use_person_list=True here?
        # TEST 1: set use_person_list to False
        print("yes reached this point from here")
        res_dict = remerge_single_group(
            group, vorfins=vorfin_list, use_person_list=True, groups_to_delete=groups_to_delete)
        new_vorfin = res_dict.get("new_vorfin")
        msg = f"Merged {group} ({group.name}) into new vorfin: {new_vorfin} ({new_vorfin.id}).\nDeleted old vorfin: {old_vorfin_name} ({old_vorfin_id})."
    except Exception as e:
        logger.info("yes, this error was raised")
        msg = f"merge failed for group_id: {group.id}, error was:\n {e}"
        raise Exception(msg)

        # return HttpResponse(f"{ELM.log_report()}\n\n{ELM.log_details()}")

    def df_to_html(df):
        if df is None or df.empty:
            return empty_result
        else:
            return df.to_html(classes="table table-sm", border=None, justify="left", index=False)

    result = {
        "msg": msg,
        "success": True,
        "rels_changed": {
            "title": "Relations with changed vorfins",
            "table": df_to_html(res_dict.get("changed_vorfins")),
        },
        "rels_added": {
            "title": "Re-added Relations",
            "table": df_to_html(res_dict.get("created_rels")),
        },
        "new_vorfin": str(res_dict["new_vorfin"]),
        "new_vorfin_id": res_dict["new_vorfin_id"],
    }

    vorfin_list = []

    return result


@shared_task
def merge_groups_task(name, groups, singles):

    def create_new_buttons(group):

        for btn in StatusButtonGroupType.objects.all():
            b, c = StatusButtonGroup.objects.get_or_create(
                kind=btn, related_instance=group)
            b.save()

            group.save()

    new_group = Group.objects.create(name=name)
    log_groups = []

    old_vorfins = []

    def get_vorfin_of_group(group):
        if group.vorfin:
            return group.vorfin
        else:
            # print(f"ADDITONAL LOGIC: Group {group} had no vorfin. Returnin None")
            return None

    groups_to_delete = []
    if groups:
        for g in groups:
            # fetch vorfins here
            # send vorfin rels
            # print(f"in merge groups function in views.py: id of group was: {g}")
            group = Group.objects.get(id=g)

            old_vorfin = get_vorfin_of_group(group)
            # TODO: check! I am not doing anything with the old vorfin list
            # TODO: use the groups_to_delete list, and restore vorfins in remerge_group tasks. Then add relations to list for check and then delete both, old vorfin and old groups
            if old_vorfin:
                old_vorfins.append(old_vorfin)

            log_groups.append((group.id, group.name))
            for m in group.members.all():
                new_group.members.add(m)
            note = group.note
            if note and new_group.note:
                new_group.note += f"\n[[ Notes from merged group ({g}):{note}]]"
            elif note:
                new_group.note = f"[[ Notes from merged group ({g}):{note}]]"

            new_group.save()
            # log.info(f"Deleted Group {group.id} with name {group.name} because group was merged into {new_group.id} with name {new_group.name}", extra={"user":request.user, "action": "Deleted Group"})

            # removed deletion of groups to after the remerge ran, because the vorfins passed along need access to old group.
            # groups_to_delete must be an array of group-ids, to make them serializable
            groups_to_delete.append(group.id)

    if singles:
        for s in singles:
            pp = PersonProxy.objects.get(person__id=s)
            pp.status = "candidate"
            pp.save()
            new_group.members.add(pp)
        new_group.save()

    new_group._gender = new_group.members.all()[0].person.gender
    new_group.save()
    create_new_buttons(new_group)

    logger.info(f"{groups_to_delete}")
    result = {
        "group_data": {
            "remove_groups": groups,
            "remove_singles": singles,
            "add": [new_group.id, new_group.name, new_group.count],
            "groups_to_delete": groups_to_delete
        },
        # "remerge_data" : remerge_data,
    }

    return result
