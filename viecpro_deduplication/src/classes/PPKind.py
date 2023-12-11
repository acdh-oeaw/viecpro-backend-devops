from . import PPHelper, PersonType, Enum, Group


class PPKind(Enum):
    # expect relation     VORVOR = "vorfinA - vorfinB"
    DUBDUB = "dubletteA - dubletteB"
    DUBSAME = "dubletteA - dubletteA"  # expect relation    VORSAME
    DUBSING = "dublette - single"  # expect relation VORSING
    SINGDUB = "single - dublette"  # expect relatio SINGVOR
    VORVOR = "vorfinA - vorfinB"  # outcome of DUBDUB
    VORSAME = "vorfinA - vorfinA"  # outcome of DUBSAME
    SINGVOR = "single - vorfin"  # outcome of SINGDUB
    VORSING = "vorfin - single"  # outcome of DUBSING
    SINGSING = "single - single"  # should not occur in script
    # should not occur in script, or how could this happen? should be VORVOR or VORSAME
    DUBVOR = "dublette - vorfin"
    # should not occur in script; should be VORVOR or VORSAME
    VORDUB = "vorfin - dublette"
    SINSING = "singleA - singleB"  # should not occur in script
    SINGSAME = "singleA - singleA"  # should not occur in script

    @classmethod
    def classify(cls, rel, in_step="external call", strict=False):
        """
        Main Method to classify a given PersonPerson relation, 
        by classifying the participating entities (persons) first.

        @param strict: if set to True, throws an error if a classification does not conform to our expectations. 
        --> must be False when processing manually created relations; we know, that they contain 
        classifications that we want to get rid of, but we want them to be logged and written first.

        """

        perA = rel.related_personA
        perB = rel.related_personB
        atype = PersonType.classify(perA, strict=strict)
        btype = PersonType.classify(perB, strict=strict)

        if atype == PersonType.DUBLETTE == btype:
            aprox = perA.personproxy
            bprox = perB.personproxy
            agroup = Group.objects.get(members__in=[aprox])
            bgroup = Group.objects.get(members__in=[bprox])

            if agroup == bgroup:
                return cls.DUBSAME
            else:
                return cls.DUBDUB

        # This part is new to catch also VORSAME in classification
        elif atype == PersonType.VORFIN == btype:
            if perA == perB:
                return cls.VORSAME
            else:
                return cls.VORVOR
        # end of new part.

        # last addition:
        elif atype == PersonType.SINGLE == btype:
            if perA == perB:
                return cls.SINGSAME
            else:
                return cls.SINGSING

        # end of last addition

        else:
            res = PPHelper._kindmap.get((atype, btype), None)
            if res:
                if res in [cls.SINGSING, cls.DUBVOR, cls.VORDUB]:
                    msg = f"In rel classify '{in_step}': res was {res}. This should not happen. Relation was: {rel} ({rel.id})."
                    PPHelper.enum_errors["Strict classification error"].append(
                        msg)
                    if strict:
                        raise Exception(msg)
                    # note: changed this here I. My guess is: the error occurs after the relation has been created.
                    # Therefore: this didn't return before and so there was no kind. This prevented the
                    # expectation missmatch to kick in .

                return res

            else:
                msg = f"Could not classify relation: {rel}. Res was: {res}.\nTypes where a:{atype}, b:{btype}."
                PPHelper.enum_errors["Classification error: No result"].append(
                    msg)
                raise Exception(msg)


