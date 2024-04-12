
from enum import StrEnum

class GroupActions(StrEnum):
    remove_member_or_members = "remove_member_s"
    merge_into_vorfin = "merge_into_vorfin"
    remerge_vorfin = "remerge_vorfin"
    dissolve_group = "dissolve_group"



def merge_group_into_vorfin(vorfin_name, group):
    pass

def remerge_group_vorfin(group, old_vorfin):
    delete_vorfin(old_vorfin)
    new_vorfin = merge_group_into_vorfin(vorfin_name, group)


def remove_member_or_members(group, members_to_remove):
    for proxy in members_to_remove:
        remove_member_from_group(group, proxy)
        set_proxy_status_to_single(proxy)
        remove_merged_into_relations(proxy, group.vorfin)

    remerge_group_vorfin(group)

def dissolve_group(group):
    for proxy in group.members.all():
        remove_member_from_group(group, proxy)
        set_proxy_status_to_single(proxy)

    delete_vorfin(group.vorfin)
    delete_group(group)



class GlobalActions(StrEnum):
    merge_all = "merge_all"
    group_selected = "group_selected"


def action_merge_all(singles, groups):
    vorfins = [g.vorfin for g in groups.keys()]
    proxies = []
    for group in groups:
        for proxy in group.members.all():
            remove_member_from_group(group, proxy)
            set_proxy_status_to_single(proxy)
            remove_merged_into_relations(proxy, group.vorfin)
            proxies.append(proxy)
        delete_group(group)


    proxies = [set_proxy_status_to_single(proxy) for proxy in proxies]

    new_group = make_group_from_singles(new_group_name, proxies)
    vorfin = merge_group_into_vorfin(new_group)


def action_group_selected(singles, groups):
    groups_with_selected_members = filter(lambda x: x.members !== [], groups)
    singles_list = singles
    for group in groups_with_selected_members:
        for proxy in group.members:
            remove_member_from_group(group, proxy)
            set_proxy_status_to_single(proxy)
            singles_list.append(proxy)

        remerge_group_vorfin(group, group.vorfin)

    new_group = make_group_from_singles(group_name, singles_list)
    new_vorfin = merge_group_into_vorfin(vorfin_name, new_group)
def set_proxy_status_to_single(proxy):
    pass

def set_proxy_status_to_member(proxy):
    pass

def remove_merged_into_relations(proxy, vorfin):
    pass

def remove_member_from_group(group, member):
    pass

def add_single_to_group(group, single):
    pass

def make_group_from_singles(group_name, singles_list):
    group = Group.objects.create(name=group_name)
    for proxy in singles_list:
        group.members.add(proxy)
        set_proxy_status_to_member(proxy)
    return group

def delete_vorfin(vorfin):
    pass

def delete_group(group):
    pass
