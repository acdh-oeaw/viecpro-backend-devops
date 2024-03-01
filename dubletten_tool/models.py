from django.db import models
from apis_core.apis_entities.models import Person
from copy import deepcopy
from django.contrib.auth.models import User
# class Note(models.Model):
#     text = models.TextField(max_length=2000, null=True, blank=True)



class PersonProxy(models.Model):
    """
    Proxy model for Person instances. Holds additional data on the Persons, like notes and data that is needed for computing Suggestions (_names and first_names).
    Each Proxy-Instance is either a memeber of a group, which results in the 'status' being set to 'candidate', or not in a group with status 'single' or already merged, and thusly a 'merged'.
    Each Proxy-Instance can only be member of one group.
    """

    class Meta:
        ordering = ['person__name']

    status_choices = [
        ("candidate", "Candidate"),
        ("single", "Single"),
        ("merged", "Merged"),
    ]
    person = models.OneToOneField(
        Person, null=False, blank=False, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=300, choices=status_choices, default="single")
    marked = models.BooleanField(default=False)
    note = models.TextField(max_length=2000, null=True, blank=True)

    _names = models.JSONField(null=True)
    _first_names = models.JSONField(null=True)

    @property
    def alt_names(self):
        nach = ["alternative name", "alternativer Nachname", "Nachname verheiratet",
                "Nachname alternativ verheiratet", "Nachname alternativ vergeiratet"]
        return [l[0].strip() for l in self.person.label_set.filter(label_type__name__in=nach).values_list("label")]

    @property
    def name_verheiratet(self):
        ver = ["Nachname verheiratet", "Nachname alternativ verheiratet",
               "Nachname alternativ vergeiratet"]
        return [l[0].strip() for l in self.person.label_set.filter(label_type__name__in=ver).values_list("label")]

    @property
    def alt_first_names(self):
        return [l[0].strip() for l in self.person.label_set.filter(label_type__name="alternativer Vorname").values_list("label")]

    @property
    def names_list(self):
        name = self.person.name
        alt_names = self.alt_names
        alt_names.append(name)
        return alt_names

    @property
    def first_names_list(self):
        first_name = self.person.first_name
        alt_first_names = self.alt_first_names
        alt_first_names.append(first_name)
        return alt_first_names

    @property
    def names_set(self):
        return set(self.names_list)

    @property
    def first_names_set(self):
        return set(self.first_names_list)

    @property
    def allnames(self):
        return set(self._names)

    @property
    def allfirst_names(self):
        return set(self._first_names)

    @property
    def name(self):
        return f"{self.person.name}, {self.person.first_name}"

    def __str__(self):
        return f"<PersonProxyInstance {self.id} - proxies: <Person: {self.person} ({self.person.id})>>"

    def __repr__(self):
        return self.__str__()


class Group(models.Model):
    """
    Group: A collection of Person-Instances (PersonProxy-Instances) storing possible duplicates. 
    Each group should run through several filter, split and add processes to finally be merged into one entity. 
    A Group holds PersonProxy-Instances, which serve as proxies for the actual Person-instances.
    """

    class Meta:
        ordering = ["name"]

    status_choices_group = [
        ("unchecked", "unchecked"),
        ("checked group", "checked group"),
        ("checked for other groups", "checked for other groups"),
        ("checked all members", "checked all members"),
        ("ready to merge", "ready to merge"),
        ("merged", "merged")
    ]
    name = models.CharField(max_length=600, blank=True)
    members = models.ManyToManyField(PersonProxy, blank=True)
    status = models.CharField(
        max_length=300, choices=status_choices_group, default="unchecked")
    _gender = models.CharField(max_length=255, null=True, blank=True)
    marked = models.BooleanField(default=False)
    note = models.TextField(max_length=2000, null=True, blank=True)
    vorfin = models.OneToOneField(
        Person, null=True, on_delete=models.SET_NULL, related_name="merged_group")

    @property
    def all_notes(self):
        notes = [{"person_id": el.person.id, "note": el.note}
                 for el in self.members.all()]
        return notes

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, value):
        self._gender = value

    @property
    def buttons(self):
        return self.statusbuttongroup_set.all()

    @property
    def count(self):
        return self.members.all().count()

    @property
    def all_names(self):
        names = set()
        for m in self.members.all():
            names = names.union(m.names)

        return names

    @property
    def all_first_names(self):
        first_names = set()
        for m in self.members.all():
            first_names = first_names.union(m.first_names)

        return first_names

    def check_status(self, status_dict):
        flag = True
        for k, v in status_dict.items():
            if v == "true":
                val = True
            else:
                val = False

            if StatusButtonGroup.objects.filter(kind__id=k, value=val, related_instance=self):
                continue
            else:
                flag = False

        return flag

    def __str__(self):
        return f"<Group: {self.name} ({self.id})>"

    def __repr__(self):
        return self.__str__()


class Suggestions(models.Model):
    # todo __g.pirgie__ add name field and query Suggestions by name rather than by index!


    data = models.JSONField(null=True, blank=True)

    

class StatusButtonGroupType(models.Model):



    name = models.CharField(max_length=600, null=False, blank=False)
    short = models.CharField(max_length=4, null=False,
                             blank=False, default="BT")

    def add_to_all_groups(self):
        all_groups = Group.objects.all()
        for g in all_groups:
            sb, c = StatusButtonGroup.objects.get_or_create(
                kind=self, related_instance=g)
            sb.save()


class StatusButtonGroup(models.Model):


    kind = models.ForeignKey(StatusButtonGroupType, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(Group, on_delete=models.CASCADE)
    value = models.BooleanField(default=False)

    def toggle_status(self):
        self.value = not self.value
        self.save()


class StatusButtonProxyType(models.Model):
    

    name = models.CharField(max_length=600, null=False, blank=False)

    def add_to_all_groups(self):
        all_proxies = PersonProxy.objects.all()
        for p in all_proxies:
            sb, c = StatusButtonProxy.objects.get_or_create(
                kind=self, related_instance=p)
            sb.save()


class StatusButtonProxy(models.Model):
    
    kind = models.ForeignKey(StatusButtonProxyType, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(PersonProxy, on_delete=models.CASCADE)
    value = models.BooleanField(default=False)


class DublettenLOG(models.Model):

    msg = models.TextField(max_length=600, null=False, blank=False)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)


# class Ampel(models.Model):
#     ampel_choices = [
#         ("red", "red"),
#         ("yellow", "yellow"),
#         ("green", "green"),

#     ]
#     person = models.OneToOneField(Person, on_delete=models.CASCADE, primary_key=True)
#     status = models.CharField(max_length=300, choices=ampel_choices, default="red")
#     note = models.TextField(max_length=2000, null=True, blank=True)
