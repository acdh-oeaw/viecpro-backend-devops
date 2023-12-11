from . import ErrorLoggerMixin, rt_vorfin, ProcessingTracker, PersonPerson, PersonPersonRelation, PersonProxy, defaultdict, log, PPKind, PPHelper


class RelationWriter(ErrorLoggerMixin):
  

    @classmethod
    def setup(cls):
        cls.errors = defaultdict(list)
        cls.enum_errors = defaultdict(list)


    @classmethod 
    def reset(cls):
        cls.setup()
        
    @classmethod
    def write_person_person_rels(cls, g):
        """
        Updated Version of the write person person rels logic. 

        Now properly takes care of the different types of persons that might be 
        participating in a PersonPerson relation.

        Main logic added is: 

        - it classifies each relation before it is written to the vorfin entry
        - it looks up and stores the expected output for each classified relation 
        - it then classifies the newly created relation and checks against the expectation

        Everything is logged to the logfile. Missmatches are visible by looking for 
        "expectation missmatch" in the logfile.

        """

        model = PersonPerson
        vorfin = g.vorfin  # Person.objects.get(id=MergeGroup.group_map[g.id])
       

        def get_dublette_or_vorfin(per):
            # called in:
            # relation writer
            res = None
            if PersonProxy.objects.filter(person=per).exists():
                proxy = PersonProxy.objects.get(person=per)

                if proxy.status == "single":
                    ##### CountPerPer.single_count += 1
                    res = per
                else:
                    gs = proxy.group_set.all()
                    if len(gs) >= 1:

                        res = gs[
                            0
                        ].vorfin  # Person.objects.get(id=MergeGroup.group_map[gs[0].id])

                    if not res:
                        cls.errors["PersonProxy lookup error in get_dublette_or_vorfin"].append(
                            f"per {per} had proxy {proxy} and was not single {proxy.status}. Group set was: {qs}.")
                        res = per

                    else:
                        # CountPerPer.member_count += 1 # Not sure what this does. Investigate and refactor.
                        pass
            else:
                res = per
            return res

        log(f"in write per per rels --> group is: {g}")
        for m in g.members.all():
            ppA = PersonPerson.objects.filter(
                related_personA=m.person).exclude(relation_type=rt_vorfin)
            ppB = PersonPerson.objects.filter(
                related_personB=m.person).exclude(relation_type=rt_vorfin)
            log(f"member is: {m} ({m.id})")
            if ppA:
                for el in ppA:
                    if el.relation_type != rt_vorfin:
                        type_of_rel_before = PPKind.classify(
                            el, in_step="PPA before")
                        ProcessingTracker.track(el, type_of_rel_before)
                        expectation = PPHelper.get_expectation(
                            type_of_rel_before)
                        log(
                            f"relation (A) of member before : {type_of_rel_before}, rel_id: {el.id}")
                        perB = get_dublette_or_vorfin(el.related_personB)
                        log(f"perB is: {perB}")
                        log(f"related_personA is {vorfin}")
                        temp = {
                            # INSERT EXPECTED RELATION OUTCOME HERE AND TEST AGAINST IT
                            "relation_type": el.relation_type,
                            "start_date_written": el.start_date_written,
                            "end_date_written": el.end_date_written,
                            "related_personA": vorfin,
                            "related_personB": perB,
                        }
                        res, c = model.objects.get_or_create(**temp)
                        type_of_rel_after = PPKind.classify(
                            res, in_step="PPA after")
                        ProcessingTracker.add(el, res, type_of_rel_after)
                        if not type_of_rel_after in expectation:
                            msg = f"Expectation missmatch; expected {expectation}, got {type_of_rel_after} instead. before: {type_of_rel_before}"
                            log(msg)
                            cls.errors["Expectation missmatch"].append(msg)
                        log(
                            f"new A - relation created: {type_of_rel_after}, rel_id: {res.id}, created: {c}")
            if ppB:
                for el in ppB:
                    if el.relation_type != rt_vorfin:
                        type_of_rel_before = PPKind.classify(
                            el, in_step="PPB before")
                        expectation = PPHelper.get_expectation(
                            type_of_rel_before)
                        ProcessingTracker.track(el, type_of_rel_before)
                        log(
                            f"relation (B) of member before : {type_of_rel_before}, rel_id: {el.id}")
                        perA = get_dublette_or_vorfin(el.related_personA)
                        log(f"perA is: {perA}")
                        log(f"realted_personB is: {vorfin}")
                        temp = {
                            "relation_type": el.relation_type,
                            "start_date_written": el.start_date_written,
                            "end_date_written": el.end_date_written,
                            "related_personA": perA,
                            "related_personB": vorfin,
                        }
                        res, c = model.objects.get_or_create(**temp)
                        type_of_rel_after = PPKind.classify(
                            res, in_step="PPB after")
                        ProcessingTracker.add(el, res, type_of_rel_after)
                        if not type_of_rel_after in expectation:
                            msg = f"Expectation missmatch; expected {expectation}, got {type_of_rel_after} instead. before: {type_of_rel_before}"
                            log(msg)
                            cls.errors["Expectation missmatch"].append(msg)
                        log(
                            f"new B - relation created: {type_of_rel_after}, rel_id: {res.id}, created: {c}")
