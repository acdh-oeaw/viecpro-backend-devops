from . import log, defaultdict, Collection, LabelType, PersonPersonRelation, logger, PersonProxy, Person, AbstractRelation, PersonPerson, Label
from apis_bibsonomy.models import Reference
from django.contrib.contenttypes.models import ContentType
class MergeGroup:
    """
    Functions defined here handle the merging of groups into a vorfinalen eintrag (MergeGroup-Class) 
    and the writing of personperson relations in existing vorfinale Einträge from the related Group.

    This is the original Merging script, updated to better process the different kinds of Person involved in 
    PerPer Relations. 

    - also processes Uris now
    - also processes titles now

    !!!!!!!!!
    IMPORTANT: 
    IF RUN IN NOTEBOOK: the main method to writing person person rels is extracted into the RelationWriter class
    and its method is used in the script, not the one defined here !
    !!!!!!!!!

    These functions are used: 
    - in the management command to create the inital merges (merge_groups command)
    - in merge_views.py, in the remergegroupview, that can be called in the dubletten_tool frontend section. The template for the button is member_list.html, the callback function resides in tool_page.html
    """

    merged_col, c = Collection.objects.get_or_create(name="Vorfinale Einträge")
    rt_vorfin, c = PersonPersonRelation.objects.get_or_create(
        name="data merged from", name_reverse="merged into"
    )
    lt_group, c = LabelType.objects.get_or_create(
        name="Result of deduplication Group")
    lt_first_name_alt, c = LabelType.objects.get_or_create(
        name="alternativer Vorname")
    lt_name_alt, c = LabelType.objects.get_or_create(
        name="alternativer Nachname")
    lt_sd_alt, c = LabelType.objects.get_or_create(
        name="alternatives Geburtsdatum")
    lt_ed_alt, c = LabelType.objects.get_or_create(
        name="alternatives Sterbedatum")
    # group_map = {} unused, therefore removed

    rels = [
        "PersonInstitution",
        "PersonPlace",
        "PersonEvent",
        "PersonWork",
        "PersonPerson",
    ]  # Handle seperately:, "PersonPerson"]

    def __init__(self, group, create=False):
        self.group = group
        self.members = [m.person for m in group.members.all()]
        self.meta = {
            "name": self.members[0].name,
            "first_name": self.members[0].first_name,
            "gender": self.group.gender,
        }
        self.create = create
        self.titles = []
        # self.additional_labels = []

    def process_names(self):
        for m in self.members[1:]:
            self.labels[MergeGroup.lt_first_name_alt].append(
                {"label": m.first_name})
            self.labels[MergeGroup.lt_name_alt].append({"label": m.name})

    def process_birth_and_death(self):
        start_dates = set()
        end_dates = set()
        alt_start, alt_end = None, None
        for m in self.members:
            if m.start_date_written:
                start_dates.add(m.start_date_written)
            if m.end_date_written:
                end_dates.add(m.end_date_written)

        start_dates = list(start_dates)
        end_dates = list(end_dates)

        if start_dates:
            if len(start_dates) == 1:
                start_date = start_dates[0]
            else:
                start_date = start_dates[0]
                alt_start = start_dates[1:]

            #  start_date, *alt_start = [start_dates]

        else:
            start_date = None

        if end_dates:
            if len(end_dates) == 1:
                end_date = end_dates[0]
            else:
                end_date = end_dates[0]
                alt_end = end_dates[1:]
        else:
            end_date = None

        self.meta.update(
            {"start_date_written": start_date, "end_date_written": end_date}
        )

        # todo: create labels from alternative start and end date lists
        if alt_start:
            for sd in alt_start:
                self.labels[MergeGroup.lt_sd_alt].append({"label": sd})
        if alt_end:
            for ed in alt_end:
                self.labels[MergeGroup.lt_ed_alt].append({"label": ed})

            # self.additional_labels.append(label_type=MergeGroup.lt_ed_alt, label=ed)

    def process_labels(self):
        labels = defaultdict(list)
        for m in self.members:
            [
                labels[el.label_type].append(
                    {
                        "label": el.label.strip(),
                        "start_date_written": el.start_date_written,
                        "end_date_written": el.end_date_written,
                    }
                )
                for el in m.label_set.all()
            ]
        # print("labels is", labels, labels.items())

        return labels

    def process_personinstitution(self):
        pass

    def process_all_other_relations(self):
        # todo: alle relations deduplizieren
        for m in self.members:
            for r in MergeGroup.rels:
                # print("r is:", r)
                if r != "PersonPerson":
                    temp = getattr(m, r.lower() + "_set").values()
                    model = AbstractRelation.get_relation_class_of_name(r)
                    # print(temp)
                    for t in temp:
                        t.pop("related_person_id")
                        t.pop("tempentityclass_ptr_id")
                        t.pop("id")
                        t["related_person"] = self.person
                        # print(t)
                        model.objects.get_or_create(**t)
                elif r == "PersonPerson":
                    # for d in ["personA_set", "personB_set"]:
                    # tempA = m.personA_set.values()
                    # tempB = m.personB_set.values()
                    pass

                    # for t in tempA:
                    #     print(t)
                    #     t.pop("related_personA_id")
                    #     t.pop("tempentityclass_ptr_id")
                    #     t.pop("id")
                    #     t["related_personA"] = self.person
                    #     #print(t)
                    #     model.objects.get_or_create(**t)
                    # for t in tempB:
                    #     print(t)
                    #     t.pop("related_personB_id")
                    #     t.pop("tempentityclass_ptr_id")
                    #     t.pop("id")
                    #     t["related_personB"] = self.person
                    #     #print(t)
                    #     model.objects.get_or_create(**t)

    def process_titles(self):
        titels = set()
        for m in self.members:
            [titels.add(t) for t in m.title.all()]

        return titels

    def process_notes(self):
        notes = ""
        for m in self.members:
            if m.notes:
                notes += f"[{m.pk}: {m.notes}]\n"
        return notes

    def process_references(self):
        print("called fetching references")
        refs = ""
        for m in self.members:
            if m.references:
                refs += f"[{m.pk}: {m.references}]\n"
        return refs

    def process_uris(self):
        uris = set()
        for m in self.members:
            for uri in m.person.uri_set.all():
                if uri.domain != "apis default":
                    uris.add(uri)
        return uris

    def process_collections(self):
        # nicht nötig
        pass

    def process_bibsonomy_references(self):
        res = []
        person_content_type = ContentType.objects.get(app_label="apis_entities", model="person")
        for m in self.members:
            references = Reference.objects.filter(content_type=person_content_type, object_id=m.person.id)
            res += list(references)

        return res



    def run_process(self):

        self.labels = self.process_labels()
        self.process_names()
        self.process_birth_and_death()

        self.titles = self.process_titles()
        notes = self.process_notes()
        refs = self.process_references()
        self.meta.update({"notes": notes, "references": refs})
        per = Person.objects.create(**self.meta)
        per.name = per.name.strip() + " {vorfinal}"
        per.collection.add(MergeGroup.merged_col)
        [per.title.add(t) for t in self.titles]
        self.uris = self.process_uris()
        for uri in self.uris:
            per.uri_set.add(uri)
        bibs_refs = self.process_bibsonomy_references()
        
        per.save()

        for ref in bibs_refs:
            Reference.objects.get_or_create(bibs_url = ref.bibs_url, pages_start=ref.pages_start, pages_end=ref.pages_end, bibtex=ref.bibtex, content_type=ref.content_type, object_id=per.id, attribute=ref.attribute, folio=ref.folio, notes=ref.notes)
        # MergeGroup.group_map.update({self.group.id:per.id})
        self.group.vorfin = per
        self.group.save()
        # print("merged group")
        # create Ampel
        # ampel = Ampel.objects.create(person=per, status="red", note=self.group.note)
        # ampel.save()

        # todo: handle start and end dates of labels as tuples
        # print(self.labels, self.labels.items())
        for key, vals in self.labels.items():
            for v in vals:
                try:
                    lab, created = Label.objects.get_or_create(
                        label_type=key, temp_entity=per, **v
                    )
                except Exception as e:
                    logger.exception(e)
                    continue
                # per.label_set.add(lab)
        for m in self.members:
            PersonPerson.objects.get_or_create(
                related_personA=per,
                related_personB=m,
                relation_type=MergeGroup.rt_vorfin,
            )

        Label.objects.get_or_create(
            label=f"{self.group.name} ({self.group.id})",
            label_type=MergeGroup.lt_group,
            temp_entity=per,
        )
        self.person = per
        self.process_all_other_relations()
        # print("Notes:", notes, "refs:", refs)


class CountPerPer:
    single_count = 0
    member_count = 0


# def write_person_person_rels(g):
#     model = PersonPerson
#     vorfin = g.vorfin  # Person.objects.get(id=MergeGroup.group_map[g.id])
#     print("vorfin is", vorfin)
#     rt_vorfin, c = PersonPersonRelation.objects.get_or_create(
#         name="data merged from", name_reverse="merged into"
#     )

#     def get_dublette_or_vorfin(per):
#         print("called get_dublette_or_vorfin with per = ", per)
#         res = None
#         if PersonProxy.objects.filter(person=per).exists():
#             print("person existed")
#             proxy = PersonProxy.objects.get(person=per)

#             if proxy.status == "single":
#                 print("personproxy status was single")
#                 CountPerPer.single_count += 1
#                 print("person was single", per)
#                 res = per
#             else:
#                 print("person status was not single")

#                 gs = proxy.group_set.all()
#                 if len(gs) > 1:
#                     print(
#                         f"personproxy {proxy} {proxy.id} was member in {gs} - this is {len(gs)}"
#                     )
#                 res = gs[
#                     0
#                 ].vorfin  # Person.objects.get(id=MergeGroup.group_map[gs[0].id])

#                 if not res:
#                     res = per
#                     print("person was not single but also not found in group")

#                 else:
#                     CountPerPer.member_count += 1
#         else:
#             print("person was no PersonProxy", per)
#             res = per
#         print("res is: ", res)
#         return res

#     for m in g.members.all():
#         ppA = PersonPerson.objects.filter(related_personA=m.person)
#         ppB = PersonPerson.objects.filter(related_personB=m.person)
#         print("member is", m)
#         print(f"ppA {ppA}, ppB {ppB}")
#         if ppA:
#             for el in ppA:
#                 print("in ppA, el is: ", el)
#                 if el.relation_type != rt_vorfin:
#                     perB = get_dublette_or_vorfin(el.related_personB)
#                     print("perB is: ", perB)
#                     print("related_personA is ", vorfin)
#                     temp = {
#                         "relation_type": el.relation_type,
#                         "start_date_written": el.start_date_written,
#                         "end_date_written": el.end_date_written,
#                         "related_personA": vorfin,
#                         "related_personB": perB,
#                     }
#                     model.objects.get_or_create(**temp)
#         if ppB:
#             for el in ppB:
#                 print("in ppB, el is: ", el)
#                 if el.relation_type != rt_vorfin:
#                     perA = get_dublette_or_vorfin(el.related_personA)
#                     print("perA is: ", perA)
#                     print("realted_personB is: ", vorfin)
#                     temp = {
#                         "relation_type": el.relation_type,
#                         "start_date_written": el.start_date_written,
#                         "end_date_written": el.end_date_written,
#                         "related_personA": perA,
#                         "related_personB": vorfin,
#                     }
#                     model.objects.get_or_create(**temp)
