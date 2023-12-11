from viecpro_deduplication.src.classes import MergeGroup, function_timer, TempRel, ErrorLoggerMixin, PersonHelper, PPHelper, logger, rt_vorfin, time, ProcessingTracker, RelationWriter
from time import time
from viecpro_deduplication.models import Group


def remerge_single_group(group, vorfins=None, use_person_list=False, groups_to_delete=[]):
    """
    Todo: wrap in error handling that resets all classes accordingly (would be a use-case for a context-manager)
    Todo: fetch the re-created and or changed rel data-frames and display them in browser after remerge.
    """

    # setup classes
    TempRel.setup()
    RelationWriter.setup()

    old_vorfin = None
    print("in remerge_single_group, vorfins is: ",
          vorfins, "group is:", group, type(group))
    if not vorfins:
        old_vorfin = group.vorfin

        # fetch and store all relations from old vorfin
        if old_vorfin:
            all_rels = old_vorfin.get_related_relation_instances()
            for rel in all_rels:
                all_rels = filter(lambda x: x.relation_type !=
                                  rt_vorfin, all_rels)
                # if rel.relation_type != rt_vorfin:
                #     TempRel(rel)

    else:
        all_rels = []
        for vorfin in vorfins:
            v_rels = vorfin.get_related_relation_instances()
            all_rels += [rel for rel in v_rels if rel.relation_type != rt_vorfin]
        if hasattr(group, "vorfin") and group.vorfin:
            # TODO: check this, I added this....
            print("yes, group.vorfin exists, adding group.vorfin rels to all rels")
            [all_rels.append(rel) for rel in group.vorfin.get_related_relation_instances(
            ) if rel.relation_type != rt_vorfin]
        else:
            print("XXXXX ---- no, this new branch was not used.")

    # TODO: check this. moved calculation of TempRel instances to after Personhelper colelctions where updated.

    personlist = set(())

    def add_all_related_persons_to_personlist(rel):
        # if hasattr(rel, "related_person"):
        #     personlist.add(rel.related_person)
        # if hasattr(rel, "related_personA"):
        #     personlist.add(rel.related_personA)
        # if hasattr(rel, "related_personB"):
        #     personlist.add(rel.related_personB)
        pass

    before = time()

    if use_person_list:
        print("Using Personlist to Calculate Persontypes")
        if vorfins:
            pass
            # [personlist.add(vorf) for vorf in vorfins]
        if old_vorfin:
            pass
            # personlist.add(old_vorfin)

        for rel in all_rels:
            add_all_related_persons_to_personlist(rel)

        # PersonHelper.update_collections(personlist=personlist)

    else:
        print("Using all Person objects to calculate Persontypes")
        # PersonHelper.update_collections()
        [TempRel(rel) for rel in all_rels]
    after = time()

    # create new vorfin

    mg = MergeGroup(group)
    mg.run_process()

    if not vorfins and old_vorfin:
        # TODO: I think this is in the wrong place. The old vorfins must be deleted before the collections are updated.
        # delete old vorfin
        # if personlist:
        #    personlist.discard(old_vorfin)
        old_vorfin.delete()
    elif not vorfins and not old_vorfin:
        print("vorfins was false and no old_vorfin")
    else:
        print("vorfins true, old vorfin false")
        print("deleting old vorfins:", vorfins)
        # if personlist:
        #    [personlist.discard(v) for v in vorfins]

        [v.delete() for v in vorfins]

    if groups_to_delete:
        print("groups_to_delete was true in remerge_single_group")
        to_del = [Group.objects.get(id=g) for g in groups_to_delete]

        for el in to_del:
            print("deleting group", el)
            el.delete()

    # if personlist:
    #     #personlist.add(mg.person)
    #     # Update the PersonHelper collections to include new vorfin
    #     # TODO: old vorfin or vorfins must be deleted, before updating collections
    #     # TODO: changed this, forgot it before
    #     PersonHelper.update_collections(personlist=personlist)
    # else:
    #     PersonHelper.update_collections()

    # create perper relations
    try:
        RelationWriter.write_person_person_rels(group)
    except Exception as e:
        print(e)

    ProcessingTracker.log()

    # re-write old relations
    # TODO: test what happens on merge of new group, that has no vorfin and no vorfins. IF this can even happen.
    TempRel.re_create_rels()
    TempRel.log_stats_report()
    RelationWriter.log_report()
    RelationWriter.log_details()

    # show which relations where re-added
    # TODO: export logs and xlsx files and offer them to download or display as html table in frontend
    # - use pandas to_html method ---

    changed_vorfins = TempRel.get_changed_edited_vorfins_dataframe()
    created_rels = TempRel.get_created_rels_dataframe()

    # reset all used classes and free the memory
    TempRel.reset()
    RelationWriter.reset()
    # TODO: ErrorLoggerMixin needs special treatment here

    # return vorfin
    new_vorfin = mg.person

    print("new_vorfin id ", new_vorfin.id)
    print(f"Calculating person-type collections took: {after-before}")
    # print(f"results in remerge single group: {type(changed_vorfins)}, {len(changed_vorfins)}, {type(created_rels)}, {len(created_rels)}")
    return {"new_vorfin": new_vorfin, "new_vorfin_id": str(new_vorfin.id), "changed_vorfins": changed_vorfins, "created_rels": created_rels}
