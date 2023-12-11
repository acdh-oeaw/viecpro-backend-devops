from . import get_ampel, Person, PersonHelper, Group, AbstractEntity, logger, PersonPerson, ErrorLoggerMixin, get_group, defaultdict, Counter, AmpelTemp, AbstractRelation, log, PersonType, PPKind, pd


class TempRel(ErrorLoggerMixin):
    """
    Helper Class that stores, classifies, and re_writes all relations that might have been 
    created after the initial merge in Vorfins with red status. 

    The idea is: 

    - it stores all data from all relations (all relation models) that red vorfins participate in.
    - it checks related_entityA and related_entityB
    - if an related entity is a VORFIN, it stores the group
    - if an related entity is a dublette, it also stores the group
    - on re-write, it fetches the newly created vorfin for each group
    - and it checks if the relation is already present (get_or_create)
    - it also stores logging data and outputs a final report to the logfile
    - it also writes the re-created relations to an excel file, for manual checks.
    """

    @classmethod
    def setup(cls):
        cls._instances = []
        #_instancesA = defaultdict(list)
        #_instancesB = defaultdict(list)
        cls._created_counter = 0
        cls.created = defaultdict(list)
        cls.existed = []
        cls.created_by_model = Counter()
        cls.existed_by_model = Counter()

        cls.errors = defaultdict(list)
        cls.enum_errors = defaultdict(list)

        cls.changed_edited_vorfins = []

    @classmethod
    def reset(cls):
        cls.setup()

    def __init__(self, rel):
        """
        Stores the data for a given relation as a TempRel - Instance. 
        All instances are stored in the TempRel classes' _instances list. 
        Processing of related_entityA and related_entityB happens here.

        All fields that are to be preserved need to be stored here. 
        """
        self.model = self.get_rel_model(rel)
        ent_a, ent_b = self.get_related_entities(rel)

        # related_entityA
        self.a = TempRel.save_group_or_entity(ent_a)
        if not self.a:
            msg = f"Returned None for ent_a: {ent_a}, from rel {rel}."
            TempRel.errors["Returned None Error"].append(msg)

        # related_entityB
        self.b = TempRel.save_group_or_entity(ent_b)
        if not self.b:
            msg = f"Returned None for ent_b: {ent_b}, from rel {rel}."
            TempRel.errors["Returned None Error"].append(msg)

        # relation_type
        self.rt = rel.relation_type

        # start and end date written
        self.start_date_written = rel.start_date_written
        self.end_date_written = rel.end_date_written

        # if relation hat an active ampel status, save the status, otherwise none (used to check in re-create-part)
        if AmpelTemp.objects.filter(temp_entity=rel):
            self.ampel = rel.ampel.status
        else:
            self.ampel = None

        # store all instances in a list. they are never accessed individually, but bulk-processed
        TempRel._instances.append(self)

    def get_rel_model(self, rel):
        """
        Helper to get the model of a relation.
        """
        model_name = rel.__class__.__name__
        model = AbstractRelation.get_relation_class_of_name(model_name)
        return model

    @property
    def a_name(self):
        """
        managed property to get the name of the a-side field.
        """
        return self.model.get_related_entity_field_nameA()

    @property
    def b_name(self):
        """
        managed property to get the name of the b-side field.
        """
        return self.model.get_related_entity_field_nameB()

    def get_related_entities(self, rel):
        """
        helper function to get entityA and entityB instances from relation.
        """

        ent_a = getattr(rel, self.a_name)
        ent_b = getattr(rel, self.b_name)

        if not ent_a:
            msg = f"None Error: ent_a: {ent_a}, rel: {rel}."
            TempRel.errors["Related Entity was none Error"].append(msg)
            log(msg)
        if not ent_b:
            msg = f"None Error: ent_b: {ent_b}, rel: {rel}."
            TempRel.errors["Related Entity was none Error"].append(msg)
            log(msg)

        return ent_a, ent_b

    @classmethod
    def is_vorfin(cls, ent):
        """
        Returns true if entity is a person and in vorfins.
        """
        if ent in PersonHelper._vorfins:
            return True
        else:
            return False

    @classmethod
    def vorfin_not_red_check(cls, vorfin):
        """
        expects a vorfin and returns true of the ampel of the vorfin is green or yellow.
        """
        status = get_ampel(vorfin)
        if status in ["yellow", "green"]:
            return True
        else:
            return False

    def get_dict_data(self):
        """
        helper function for serialising the stored data. 
        To allow dictionary destructuring in get_or_create.
        """

        temp = {
            "relation_type": self.rt,
            "start_date_written": self.start_date_written,
            "end_date_written": self.end_date_written,
        }

        # This part takes care of the diverging related_entity field names in Relation models.
        temp[self.a_name] = self.get_vorfin_or_entity(self.a)
        temp[self.b_name] = self.get_vorfin_or_entity(self.b)

        return temp

    @classmethod
    def save_group_or_entity(cls, ent):
        """
        Helper function that expects an entity and returns said entity, or, if it 
        is an instance of Person, checks if it is a VORFIN. if, so, returnes the group,
        instead of the entity.
        Also checks if it is a Dublette, if so, tries to get teh group and returns the group.
        """

        #log(f"in save_group_or_person, ent is {ent}")
        if isinstance(ent, Person):
            kind = PersonType.classify(ent)
            #log(f"Classified {ent} as {kind}")
            # if ent in PersonHelper._vorfins:
            if kind == PersonType.VORFIN:
                res = get_group(ent)
                #log(f"Entity was Person and was in vorfins, returning: {res}")
                return res
            # elif ent in PersonHelper._dubletten:
            if kind == PersonType.DUBLETTE:
                #log(f"kind of {ent} was Dublette, entered processing")
                # try:
                proxy = ent.personproxy
                if not proxy:
                    msg = f"No Proxy Error: person: {ent}. proxy was: {proxy}"
                    cls.errors["Dublette without proxy error"].append(msg)
                    #log(msg)
                    return ent
                groupset = proxy.group_set.all()
                if len(groupset) > 1:
                    msg = f"Dublette {ent} in manually created PP-rels has multiple groups: {groupset}. Wrote to first group"
                    cls.errors["Dublette with multiple groups Error"].append(
                        msg)
                    #log(msg)

                group = groupset[0]
                if not group:
                    msg = f"Dublette without group: {ent}, group: {group}"
                    cls.errors["Dublette without group Error"].append(msg)
                #log(f"returning group: {group}")
                return group
            else:
                #log(f"kind of person was: {kind}, returning person {ent}")
                return ent

                # except Exception as e:
                #cls.errors["Raised Exception in save_group_or_entity, in was dublette"].append(f"Exception in save_group_or... :  {e}")
                # return ent

        else:
            #log(f"Entity was no Person: {ent}, type:({type(ent)})")
            return ent

    def get_vorfin_or_entity(self, p):
        """
        Reverse helper functin of save_group_or_entity: returns the entity, or, 
        if it is a group, the newly created VORFIN.
        """
        #log(f"in get_vorfin or entity, p is {p} ({type(p)})")
        if isinstance(p, Group):
            #log(f"was instance of Group: {p}")
            try:
                group = Group.objects.get(id=p.id)
                #log(f"returning group.vorfin: {group.vorfin} ({group.vorfin.id})")
                return group.vorfin
            except Exception as e:
                TempRel.errors["Could not find group error"].append(
                    f"Could not find group for: {p}({p.id})")
                logger.exception(e)
                res = None
                #log(f"result set to {res}")
                return res
        else:
            #log(f"in else. p is {p}, type is: {type(p)}")
            if not isinstance(p, AbstractEntity):
                msg = f"Expected entity to be subclass of AbstracEntity. Got {type(p)} instead."
                TempRel.errors["Entity Expectation Error"].append(msg)
                # raise Exception(msg)
            #log(f"no exception, returning {p}.")
            return p

    @classmethod
    def re_create_rels(cls):
        """
        Main method for re-creating stored relations. Runs in bulk-processing over all instances of TempRel.
        """
        for inst in cls._instances:
            #log(f"in re_create_rels. instance is {inst}. a is : {inst.a}, atpye {type(inst.a)}, b is {inst.b}, btype {type(inst.b)}")
            a = inst.get_vorfin_or_entity(inst.a)
            b = inst.get_vorfin_or_entity(inst.b)
            if a and b:
                if not inst.model.objects.filter(**inst.get_dict_data()).exists():
                    # TODO: inspect, CHANGED THIS
                    rel, c = inst.model.objects.get_or_create(
                        **inst.get_dict_data())
                    rel.save()
                    write_to_changed_flag = False
                    for x in [a, b]:
                        if cls.is_vorfin(x) and cls.vorfin_not_red_check(x):
                            write_to_changed_flag = True
                    if c:
                        cls._created_counter += 1
                        cls.created_by_model[inst.model]
                        cls.created[inst.model].append(rel)
                        #log(f"Re-created deleted relation: {rel}. type = {inst.model.__name__}")
                        if inst.ampel:
                            AmpelTemp.objects.get_or_create(
                                temp_entity=rel, status=inst.ampel)
                        #log(f"Set ampel for new relation to: {inst.ampel}.")
                        if write_to_changed_flag:
                            cls.changed_edited_vorfins.append(rel)
                else:
                    #log(f"Relation existed: {inst}")
                    cls.existed_by_model[inst.model]
                    cls.existed.append(inst)
            else:
                #log(f"a or b was none: a:{a} b: {b}")
                pass

        #log(f"Re-created {cls._created_counter} - Relations successfully.")

    @classmethod
    def log_stats_report(cls):
        """
        Helper to log stored statistics on created relations and those that already existed.
        """

        log(f"Number of relations that already existed = {len(cls.existed)}")
        log(f"Number of relations that wher re-created = {len(cls.created)}")
        log(f"created counter: {cls._created_counter}")

        log(f"created relations by model:")
        for mod, count in cls.created_by_model.items():
            log(f"\t{mod}: {count}")

        log(f"existed relations by model:")
        for mod, count in cls.existed_by_model.items():
            log(f"\t{mod}: {count}")

        for model, rels in cls.created.items():
            if model == PersonPerson:
                for r in rels:
                    kind = PPKind.classify(r)
                    log(f"Re-created PP-relation {r}\nkind:{kind}.\n")
            else:
                for r in rels:
                    log(
                        f"Re-created relation of type: {r.__class__.__name__}. rel is: {r}")

        log(f"Changed edited vorfins {len(cls.changed_edited_vorfins)}")

    @classmethod
    def get_changed_edited_vorfins_dataframe(cls):

        def get_vorfin_ampel(per):
            """
            Helper to get ampel of vorfin entry. If entity not a vorfin:
            returns 'NO VORFIN'. Only used to write the ampel status to 
            the excel file here.
            """
            if per in PersonHelper._vorfins:
                ampel = get_ampel(per)
                return ampel
            else:
                return "NO VORFIN"

        if cls.changed_edited_vorfins:
            data = []
            for rel in cls.changed_edited_vorfins:
                model = rel.__class__
                a_name = model.get_related_entity_field_nameA()
                b_name = model.get_related_entity_field_nameB()

                ent_a = getattr(rel, a_name)
                ent_a_ampel = get_vorfin_ampel(ent_a)
                ent_b = getattr(rel, b_name)
                ent_b_ampel = get_vorfin_ampel(ent_b)
                a_id = ent_a.id
                b_id = ent_b.id
                rt = rel.relation_type.name
                sd = rel.start_date_written
                ed = rel.end_date_written

                temp = {
                    "Relation": f"{model.__name__} ({rel.id})",
                    "source": f"{ent_a} ({ent_a.id})",
                    "source ampel": ent_a_ampel,
                    "relation_type": rt,
                    "target": f"{ent_b} ({ent_b.id})",
                    "target ampel": ent_b_ampel,
                    "StartDate": sd,
                    "EndDate": ed
                }
                data.append(temp)

            df = pd.DataFrame(data)
            print("in TEmpREl changed_edited, df is:",df)
            return df

    @classmethod
    def get_created_rels_dataframe(cls):
        data = []
        for model, rels in cls.created.items():
            a_field = model.get_related_entity_field_nameA()
            b_field = model.get_related_entity_field_nameB()

            for r in rels:
                ent_a = getattr(r, a_field)
                ent_b = getattr(r, b_field)
                #print(ent_a, type(ent_a))

                temp = {
                    "Relation": f"{model.__name__} ({r.id})",
                    "source": f"{ent_a} ({ent_a.id})",
                    "relation_type": r.relation_type.name,
                    "target": f"{ent_b} ({ent_b.id})",
                    "start": r.start_date_written,
                    "end": r.end_date_written,
                    "rel_class": "None"
                }
                # temp[a_field] = ent_a
                # temp[a_field+"_id"] = ent_a.id
                # temp[b_field] = ent_b
                # temp[b_field+"_id"] = ent_b.id

                # temp["source"] = ent_a
                # temp["source"+"_id"] = ent_a.id
                # temp["target"] = ent_b
                # temp["target"+"_id"] = ent_b.id

                if model == PersonPerson:
                    kind = PPKind.classify(r)
                    temp["rel_class"] = kind

                data.append(temp)

        df = pd.DataFrame(data)
        print("in TEmpREl created_rels, df is:",df)


        return df

    @classmethod
    def write_changed_edited_vorfins_to_excel(cls):
        """
        Writes collected relations in which already edited vorfins participate to an xlsx file.
        """
        df = cls.get_changed_edited_vorfins_dataframe()
        df.to_excel(
            "../../data/output/relations_that_changed_edited_vorfins.xlsx")

    @classmethod
    def write_created_to_excel(cls, filename="manually_created_rels_check.xlsx"):
        """
        Helper function to export the list of newly created relations as a xlsx - file. 
        """

        if not filename.endswith(".xlsx"):
            filename = filename + ".xlsx"

        df = cls.get_created_rels_dataframe()
        df.to_excel(f"../../data/output/{filename}", index=False)

    def __str__(self):
        return f"<TempRel: {self.a} - {self.rt} - {self.b}>"

    def __repr__(self):
        return self.__str__()
