# -*- coding: utf-8 -*-
import copy
import logging
from crispy_forms.layout import Layout, Fieldset, Submit, Button, Field
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Button, Submit
from dal import autocomplete
import re
import sys
import inspect
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.forms import ModelMultipleChoiceField, ModelChoiceField, HiddenInput
from django.urls import reverse
from django import forms

from apis_core.apis_metainfo.models import TempEntityClass, Text, Uri, Collection
from apis_core.apis_relations.forms2 import validate_target_autocomplete
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import VocabsBaseClass, AbstractRelationType
from apis_core.apis_labels.forms import LabelForm
from viecpro_import.tables import get_generic_relations_table


from apis_core.helper_functions import DateParser
from apis_core.helper_functions.RDFParser import RDFParser
from apis_core.apis_entities.fields import ListSelect2, Select2Multiple
from apis_core.apis_entities.models import AbstractEntity
from .models import DataSource, ImportProject

log = logging.getLogger("mylogger")
log.setLevel(logging.INFO)


class EditDataSourceForm(forms.ModelForm):
    class Meta:
        model = DataSource

        fields = ["name", "citation", "year", "server_directory", "page_count"]

    def __init__(self, *args, **kwargs):
        super(EditDataSourceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.from_tag = False
        self.helper.form_class = "update_datasource_form"
        self.helper.layout = Layout(
            "name", "citation", "year", "server_directory", "page_count")
        self.helper.form_method = "POST"
        self.helper.add_input(
            Submit("submit", "save", css_id="post_update_datasource"))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-danger',
                                     onclick="updateBrowserPage()"))


class CreateImportProjectForm(forms.ModelForm):
    class Meta:
        model = ImportProject
        fields = ["name", "description", "Editors", "DataSources", "owner"]

    def __init__(self, user=None, *args, **kwargs):
        super(CreateImportProjectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        ds = DataSource.objects.filter(owner=user)
        ed = User.objects.exclude(pk=user.pk)
        self.fields["owner"].widget = HiddenInput()
        self.fields["owner"].initial = user.pk

        if ds:
            self.fields["DataSources"].queryset = ds
            self.helper.layout = Layout(
                "name", "description", "Editors", "DataSources", "owner")
        else:
            del self.fields["DataSources"]
            self.helper.layout = Layout(
                "name", "description", "Editors", "owner")

        if ed:
            self.fields["Editors"].queryset = ed
            self.helper.layout = Layout(
                "name", "description", "Editors", "DataSources", "owner")
        else:
            del self.fields["Editors"]
            self.helper.layout = Layout(
                "name", "description", "DataSources", "owner")

        # self.helper.form_tag = False
        self.helper.form_method = "POST"
        self.helper.add_input(Submit("submit", "Submit"))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-danger',
                                     onclick="window.location.href = '{}';".format(
                                             reverse('viecpro_import:project_main'))))


class UploadFileForm(forms.Form):
    """
    Combines two models:
    names, citation and year are fields in DataSource
    file is processed and then split into DataSourcePageObjects
    """
    name = forms.CharField(max_length=50)
    citation = forms.CharField(max_length=500)
    year = forms.CharField(max_length=10)
    server_directory = forms.CharField(max_length=255)
    page_count = forms.IntegerField(max_value=10000)

    def __init__(self, *args, project_pk, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.from_tag = False
        self.helper.layout = Layout(
            "name", "citation", "year", "server_directory", "page_count")
        self.helper.add_input(Submit("submit", "Submit"))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-danger',
                                     onclick="updateBrowserPage(null, null)"))


def get_custom_generic_entities_form(entity):
    # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function/class if possible

    class CustomGenericEntitiesForm(forms.ModelForm):
        class Meta:
            model = AbstractEntity.get_entity_class_of_name(entity)

            exclude = [
                "start_date",
                "start_start_date",
                "start_end_date",
                "start_date_is_exact",
                "end_date",
                "end_start_date",
                "end_end_date",
                "end_date_is_exact",
                "text",
                "source",
                "published",
            ]
            exclude.extend(model.get_related_entity_field_names())
            exclude.extend(model.get_related_relationtype_field_names())
            if entity == "Person":
                exclude += ["profession", "review", "status"]
            else:
                exclude += ["review", "status"]

        def __init__(self, *args, **kwargs):
            super(CustomGenericEntitiesForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_class = entity.title() + "Form"
            self.helper.form_tag = False
            self.helper.help_text_inline = True
            acc_grp1 = Fieldset("Metadata {}".format(entity.title()))
            # AccordionGroup("MetaInfo", "references", "notes")#, "review")
            acc_grp2 = []
            attrs = {
                "data-placeholder": "Type to get suggestions",
                "data-minimum-input-length": getattr(settings, "APIS_MIN_CHAR", 3),
                "data-html": True,
            }

            # list to catch all fields that will not be inserted into accordion group acc_grp2
            fields_list_unsorted = []

            for f in self.fields.keys():
                if isinstance(
                        self.fields[f], (ModelMultipleChoiceField,
                                         ModelChoiceField)
                ):
                    v_name_p = str(self.fields[f].queryset.model.__name__)
                    if isinstance(self.fields[f], ModelMultipleChoiceField):
                        widget1 = Select2Multiple
                    else:
                        widget1 = ListSelect2
                    if (
                            ContentType.objects.get(
                                app_label__in=[
                                    "apis_entities",
                                    "apis_metainfo",
                                    "apis_relations",
                                    "apis_vocabularies",
                                    "apis_labels",
                                ],
                                model=v_name_p.lower(),
                            ).app_label.lower()
                            == "apis_vocabularies"
                    ):
                        self.fields[f].widget = widget1(
                            url=reverse(
                                "apis:apis_vocabularies:generic_vocabularies_autocomplete",
                                kwargs={
                                    "vocab": v_name_p.lower(), "direct": "normal"},
                            ),
                            attrs=attrs,
                        )
                        if self.instance:
                            res = []
                            if isinstance(self.fields[f], ModelMultipleChoiceField):
                                try:
                                    for x in getattr(self.instance, f).all():
                                        res.append((x.pk, x.label))
                                except ValueError:
                                    pass
                                self.fields[f].initial = res
                                self.fields[f].choices = res
                            else:
                                try:
                                    res = getattr(self.instance, f)
                                    if res is not None:
                                        self.fields[f].initial = (
                                            res.pk, res.label)
                                        self.fields[f].choices = [
                                            (res.pk, res.label),
                                        ]
                                except ValueError:
                                    res = ""
                if f not in acc_grp2:
                    # append to unsorted list, so that it can be sorted and afterwards attached to accordion group
                    # acc_grp1
                    fields_list_unsorted.append(f)

            def sort_fields_list(list_unsorted, entity_label):
                """
                Sorts a list of model fields according to a defined order.


                :param list_unsorted: list
                    The unsorted list of fields.

                :param entity_label: str
                    The string representation of entity type, necessary to find the entity-specific ordering (if it
                    is defined)


                :return: list
                    The sorted list if entity-specific ordering was defined, the same unordered list if not.
                """

                sort_dic = {
                    "Person": ["first_name", "name", "start_date_written", "end_date_written", "gender",
                               "title", "collection", "references", "notes"],
                    "Place": ["name", "kind", "lat", "lng", "start_date_written", "end_date_written", "references",
                              "notes"],
                    "Institution": ["name", "kind", "start_date_written", "end_date_written", "references", "notes"],
                    "Work": ["name", "kind", "start_date_written", "end_date_written", "references", "notes"],
                    "Event": ["name", "kind", "start_date_written", "end_date_written", "references", "notes"],
                }

                sort_preferences = sort_dic.get(entity_label)

                sort_preferences_used = []

                if sort_preferences is None:
                    return list_unsorted
                else:
                    # list of tuples to be sorted later
                    field_rank_pair_list = []
                    for field in list_unsorted:
                        if field in sort_preferences:
                            # if this succeeds, then the field has been given a priorites ordering above
                            ranking_by_index = sort_preferences.index(field)
                            sort_preferences_used.append(field)
                            field_rank_pair = (field, ranking_by_index)
                        else:
                            # if no ordering for the field was found, then give it 'Inf'
                            # so that it will be attached at the end.
                            field_rank_pair = (field, float('Inf'))
                        field_rank_pair_list.append(field_rank_pair)
                    # Make a check if all items of sort_preferences were used. If not, this indicates an out of sync
                    # setting
                    # if len(sort_preferences) > 0:
                    if len(sort_preferences_used) != len(sort_preferences):

                        differences = []
                        for p in sort_preferences_used:
                            if p not in sort_preferences:
                                differences.append(p)
                        for p in sort_preferences:
                            if p not in sort_preferences_used:
                                differences.append(p)

                        raise Exception(
                            "An item of the entity setting 'form_order' list was not used. \n"
                            "This propably indicates that the 'form_order' settings is out of sync with the "
                            "effective django models.\n"
                            f"The relevant entity is: {entity_label}\n"
                            f"And the differences between used list and settings list are: {differences}"
                        )
                    # sort the list according to the second element in each tuple
                    # and then take the first elements from it and return as list
                    return [t[0] for t in sorted(field_rank_pair_list, key=lambda x: x[1])]

            # sort field list, iterate over it and append each element to the accordion group

            for f in sort_fields_list(fields_list_unsorted, entity):
                acc_grp1.append(f)

            self.helper.layout = Layout(Accordion(acc_grp1))  # , acc_grp2))
            if self.fields.get("status"):
                self.fields["status"].required = False
            self.fields["collection"].required = False
            self.fields["start_date_written"].required = False
            self.fields["end_date_written"].required = False
            self.fields["name"].required = True

            instance = getattr(self, "instance", None)
            if instance != None:

                if instance.start_date_written:
                    self.fields[
                        "start_date_written"
                    ].help_text = DateParser.get_date_help_text_from_dates(
                        single_date=instance.start_date,
                        single_start_date=instance.start_start_date,
                        single_end_date=instance.start_end_date,
                        single_date_written=instance.start_date_written,
                    )
                else:
                    self.fields[
                        "start_date_written"
                    ].help_text = DateParser.get_date_help_text_default()

                if instance.end_date_written:
                    self.fields[
                        "end_date_written"
                    ].help_text = DateParser.get_date_help_text_from_dates(
                        single_date=instance.end_date,
                        single_start_date=instance.end_start_date,
                        single_end_date=instance.end_end_date,
                        single_date_written=instance.end_date_written,
                    )
                else:
                    self.fields[
                        "end_date_written"
                    ].help_text = DateParser.get_date_help_text_default()

        def save(self, *args, **kwargs):
            obj = super(CustomGenericEntitiesForm, self).save(*args, **kwargs)
            if obj.collection.all().count() == 0:
                col_name = getattr(
                    settings, "APIS_DEFAULT_COLLECTION", "manually created entity"
                )
                col, created = Collection.objects.get_or_create(name=col_name)
                obj.collection.add(col)
            return obj

    return CustomGenericEntitiesForm


class GenericEntitiesStanbolForm(forms.Form):
    # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function/class if possible

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        entity = RDFParser(cd["entity"], self.entity.title()).get_or_create()
        return entity

    def __init__(self, entity, *args, **kwargs):

        attrs = {
            "data-placeholder": "Type to get suggestions",
            "data-minimum-input-length": getattr(settings, "APIS_MIN_CHAR", 3),
            "data-html": True,
            "style": "width: auto",
        }
        ent_merge_pk = kwargs.pop("ent_merge_pk", False)
        super(GenericEntitiesStanbolForm, self).__init__(*args, **kwargs)
        self.entity = entity
        self.helper = FormHelper()
        form_kwargs = {"entity": entity}
        url = reverse(
            "apis:apis_entities:generic_entities_autocomplete",
            args=[entity.title(), "remove"],
        )
        label = "Create {} from reference resources".format(entity.title())
        button_label = "Create"
        if ent_merge_pk:
            form_kwargs["ent_merge_pk"] = ent_merge_pk
            url = reverse(
                "apis:apis_entities:generic_entities_autocomplete",
                args=[entity.title(), ent_merge_pk],
            )
            label = "Search for {0} in reference resources or db".format(
                entity.title())
            button_label = "Merge"
        self.helper.form_action = reverse(
            "apis:apis_entities:generic_entities_stanbol_create", kwargs=form_kwargs
        )
        self.helper.add_input(Submit("submit", button_label))
        self.fields["entity"] = autocomplete.Select2ListCreateChoiceField(
            label=label,
            widget=ListSelect2(url=url, attrs=attrs),
            validators=[URLValidator],
        )


############### Create Forms Generic Section ####################
def get_subclass_dic(superclass, module):
    classes_in_module = [(name, object) for name,
                         object in inspect.getmembers(module, inspect.isclass)]
    subclass_dic = {key: val for key,
                    val in classes_in_module if superclass.__subclasscheck__(val)}

    return subclass_dic


def get_model_class_of_name(superclass, module, model_name):
    module = sys.modules[module]
    subclass_dic = get_subclass_dic(superclass, module)
    res = subclass_dic[model_name]

    return res


class GenericLabelForm(LabelForm):
    pass


#
#     def __init__(self, *args, **kwargs):
#         super(GenericLabelForm, self).__init__(*args, **kwargs)
#         self.helper.form_tag = True
#         self.helper.form_method = "post"
#         self.helper.form_action = f"/viecpro_import/create_item/Label"

def get_generic_vocabs_form(model_name):
    module = "apis_core.apis_vocabularies.models"
    "Returns a form for all models ending with -Type (i.e. 'TextType', 'CollectionType', 'InstitutionType'), " \
        "plus also the 'Title' model."

    class GenericVocabsForm(forms.ModelForm):
        class Meta:
            model = get_model_class_of_name(
                VocabsBaseClass, module, model_name)
            fields = ["name"]

        def __init__(self, *args, **kwargs):
            super(GenericVocabsForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.add_input(
                Submit("submit", "save", css_class=f"{model_name}Form"))
            self.helper.form_method = "post"
            self.helper.form_class = "form pdf_tool_itemcreate"
            self.helper.form_action = reverse("viecpro_import:item_create", kwargs={
                                              "model_name": model_name})
            self.helper.layout = Layout(Field("name",
                                              id=f"{model_name}_name_field"))

    return GenericVocabsForm


def get_generic_relationtype_form(model_name):
    "Returns a form for all models ending with -Relation (i.e. 'PersonInstitutionRelation', etc.)"
    module = "apis_core.apis_vocabularies.models"

    class GenericRelationTypeForm(forms.ModelForm):
        class Meta:
            model = get_model_class_of_name(
                AbstractRelationType, module, model_name)
            # todo: check if more fields should be added
            fields = ["name", "name_reverse"]

        def __init__(self, *args, **kwargs):
            super(GenericRelationTypeForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.add_input(
                Submit("submit", "save", css_class=f"{model_name}Form"))
            self.helper.form_method = "post"
            self.helper.form_class = "form pdf_tool_itemcreate"
            self.helper.form_action = reverse("viecpro_import:item_create", kwargs={
                                              "model_name": model_name})
            self.helper.layout = Layout(Field("name", id=f"{model_name}Form_name_field"),
                                        Field("name_reverse", id=f"{model_name}Form_name_reverse_field"))
            self.fields["name_reverse"].required = False

    return GenericRelationTypeForm


def get_generic_entity_type_form(model_name):
    module = "apis_core.apis_vocabularies.models"

    class GenericEntityTypeForm(forms.ModelForm):
        class Meta:
            model = get_model_class_of_name(
                VocabsBaseClass, module, model_name)
            # todo: check if more fields should be added
            fields = ["name", "description"]

        def __init__(self, *args, **kwargs):
            super(GenericEntityTypeForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.add_input(
                Submit("submit", "save", css_class=f"{model_name}Form"))
            self.helper.form_method = "post"
            self.helper.form_class = "form pdf_tool_itemcreate"
            self.helper.form_action = reverse("viecpro_import:item_create", kwargs={
                                              "model_name": model_name})
            self.helper.layout = Layout(Field("name", id=f"{model_name}Form_name_field"),
                                        Field("description", id=f"{model_name}Form_description_field"))
            self.fields["description"].required = False

    return GenericEntityTypeForm


class CustomGenericRelationForm(forms.ModelForm):
    class Meta:
        model = TempEntityClass
        fields = ['start_date_written',
                  'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
        }

    def save(self, site_instance, instance=None, commit=True):
        """
        Save function of the GenericRelationForm.
        :param site_instance: Instance where the form is used on
        :param instance: PK of the relation that is saved
        :param commit: Whether to already commit the save.
        :type site_instance: object
        :type instance: int
        :type commit: bool
        :rtype: object
        :return: instance of relation
        """
        cd = self.cleaned_data
        if instance:
            x = self.relation_form.objects.get(pk=instance)
        else:
            x = self.relation_form()
        x.relation_type_id = cd['relation_type']
        x.start_date_written = cd['start_date_written']
        x.end_date_written = cd['end_date_written']
        x.notes = cd['notes']
        x.references = cd['references']
        setattr(x, self.rel_accessor[3], site_instance)
        target = AbstractEntity.get_entity_class_of_name(self.rel_accessor[0])
        t1 = target.get_or_create_uri(cd['target'])
        if not t1:
            t1 = RDFParser(cd['target'], self.rel_accessor[0]).get_or_create()
        setattr(x, self.rel_accessor[2], t1)
        if self.highlighter:
            an_proj = AnnotationProject.objects.get(
                pk=int(self.request.session.get('annotation_project', 1)))
            x.published = an_proj.published
        if commit:
            x.save()
        if self.highlighter:
            if not commit:
                x.save()
            txt = Text.objects.get(pk=cd['HL_text_id'][5:])
            a = Annotation(
                start=cd['HL_start'],
                end=cd['HL_end'],
                text=txt,
                user_added=self.request.user,
                annotation_project_id=int(self.request.session.get('annotation_project', 1)))
            a.entity_link = x
            a.save()
        print('saved: {}'.format(x))
        return x

    def get_text_id(self):
        """
        Function to retrieve the highlighted text.
        :return: ID of text that was highlighted
        """
        return self.cleaned_data['HL_text_id'][5:]

    def get_html_table(self, entity_type, request, site_instance, form_match):
        table = get_generic_relations_table(relation_class=self.relation_form, entity_instance=site_instance,
                                            detail=False)
        prefix = re.match(r'([A-Z][a-z])[^A-Z]*([A-Z][a-z])',
                          self.relation_form.__name__)
        prefix = prefix.group(1) + prefix.group(2) + '-'
        if form_match.group(1) == form_match.group(2):
            dic_a = {'related_' + entity_type.lower() + 'A': site_instance}
            dic_b = {'related_' + entity_type.lower() + 'B': site_instance}
            if 'apis_highlighter' in settings.INSTALLED_APPS:
                objects = self.relation_form.objects.filter_ann_proj(request=request).filter(
                    Q(**dic_a) | Q(**dic_b)
                )
            else:
                objects = self.relation_form.objects.filter(
                    Q(**dic_a) | Q(**dic_b)
                )

            table_html = table(data=objects, prefix=prefix)
        else:
            tab_query = {'related_' + entity_type.lower(): site_instance}
            if 'apis_highlighter' in settings.INSTALLED_APPS:
                ttab = self.relation_form.objects.filter_ann_proj(
                    request=request).filter(**tab_query)
            else:
                ttab = self.relation_form.objects.filter(**tab_query)
            table_html = table(data=ttab, prefix=prefix)
        return table_html

    def __init__(self, siteID=None, highlighter=False, prefill_inst=None, prefill_func=None, prefill_notes=None, *args,
                 **kwargs):
        """
        Generic Form for relations.
        :param siteID: ID of the entity the form is used on
        :param entity_type: Entity type of the entity the form is used on
        :param relation_form: Type of relation form.
        :param instance: instance of relation.
        :param highlighter: whether the form is used in the highlighter
        :type siteID: int
        :type entity_type: object or int
        :type relation_form: object or int
        :type instance: object
        :type highlighter: bool
        """

        attrs = {
            'data-placeholder': 'Type to get suggestions',
            'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
            'data-html': True,
            'style': 'width: 100%'
        }
        help_text_target = "Search and select or use an URL from a reference resource"
        attrs_target = copy.deepcopy(attrs)
        attrs_target['data-tags'] = '1'
        css_notes = 'LS'
        self.highlighter = highlighter
        entity_type = kwargs.pop('entity_type')
        if type(entity_type) != str:
            entity_type = entity_type.__name__
        self.relation_form = kwargs.pop('relation_form')
        if type(self.relation_form) == str:
            self.relation_form = AbstractRelation.get_relation_class_of_name(
                self.relation_form)
        self.request = kwargs.pop('request', False)
        super(CustomGenericRelationForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'] = forms.CharField(
            label='Relation type', required=True)
        self.helper = FormHelper()
        self.helper.form_class = '{}Form'.format(str(self.relation_form))
        self.helper.form_tag = False
        lst_src_target = re.findall(
            '[A-Z][^A-Z]*', self.relation_form.__name__)
        if lst_src_target[0] == lst_src_target[1]:
            if instance and instance.id:
                if getattr(instance, 'related_{}A_id'.format(lst_src_target[0].lower())) == int(siteID):
                    self.rel_accessor = (lst_src_target[1], True,
                                         'related_{}B'.format(
                                             lst_src_target[1].lower()),
                                         'related_{}A'.format(lst_src_target[0].lower()))
                else:
                    self.rel_accessor = (lst_src_target[1], False,
                                         'related_{}A'.format(
                                             lst_src_target[1].lower()),
                                         'related_{}B'.format(lst_src_target[0].lower()))
            else:
                self.rel_accessor = (lst_src_target[1], True,
                                     'related_{}B'.format(
                                         lst_src_target[1].lower()),
                                     'related_{}A'.format(lst_src_target[0].lower()))
            self.fields['relation_type'] = autocomplete.Select2ListCreateChoiceField(
                label='Relation type',
                widget=ListSelect2(
                    # url='/vocabularies/autocomplete/{}{}relation/normal'.format(lst_src_target[0].lower(),
                    # lst_src_target[1].lower()),
                    url=reverse('apis:apis_vocabularies:generic_vocabularies_autocomplete', args=[
                                ''.join([lst_src_target[0].lower(), lst_src_target[1].lower(), 'relation']), 'normal']),
                    attrs=attrs))
            self.fields['target'] = autocomplete.Select2ListCreateChoiceField(
                label=lst_src_target[1],
                widget=ListSelect2(
                    # url='/entities/autocomplete/{}'.format(lst_src_target[1].lower()),
                    url=reverse('apis:apis_entities:generic_entities_autocomplete',
                                args=[lst_src_target[1].lower()]),
                    attrs=attrs_target),
                validators=[validate_target_autocomplete],
                help_text=help_text_target)
        elif entity_type.lower() == lst_src_target[0].lower():
            self.rel_accessor = (lst_src_target[1], True,
                                 'related_{}'.format(
                                     lst_src_target[1].lower()),
                                 'related_{}'.format(lst_src_target[0].lower()))
            self.fields['relation_type'] = autocomplete.Select2ListCreateChoiceField(
                label='Relation type',
                widget=ListSelect2(
                    # url='/vocabularies/autocomplete/{}{}relation/normal'.format(lst_src_target[0].lower(),
                    # lst_src_target[1].lower()),
                    url=reverse('apis:apis_vocabularies:generic_vocabularies_autocomplete', args=[
                                ''.join([lst_src_target[0].lower(), lst_src_target[1].lower(), 'relation']), 'normal']),
                    attrs=attrs))
            self.fields['target'] = autocomplete.Select2ListCreateChoiceField(
                label=lst_src_target[1],
                widget=ListSelect2(
                    # url='/entities/autocomplete/{}'.format(lst_src_target[1].lower()),
                    url=reverse('apis:apis_entities:generic_entities_autocomplete',
                                args=[lst_src_target[1].lower()]),
                    attrs=attrs_target),
                validators=[validate_target_autocomplete],
                help_text=help_text_target)
        elif entity_type.lower() == lst_src_target[1].lower():
            self.rel_accessor = (lst_src_target[0], False,
                                 'related_{}'.format(
                                     lst_src_target[0].lower()),
                                 'related_{}'.format(lst_src_target[1].lower()))
            self.fields['relation_type'] = autocomplete.Select2ListCreateChoiceField(
                label='Relation type',
                widget=ListSelect2(
                    url=reverse('apis:apis_vocabularies:generic_vocabularies_autocomplete', args=[
                        ''.join([lst_src_target[0].lower(),
                                 lst_src_target[1].lower(), 'relation']),
                        'reverse']),
                    attrs=attrs))
            self.fields['target'] = autocomplete.Select2ListCreateChoiceField(
                label=lst_src_target[0],
                widget=ListSelect2(
                    # url='/entities/autocomplete/{}'.format(lst_src_target[0].lower()),
                    url=reverse('apis:apis_entities:generic_entities_autocomplete',
                                args=[lst_src_target[0].lower()]),
                    attrs=attrs_target),
                validators=[validate_target_autocomplete],
                help_text=help_text_target)
        else:
            print('no hit rel_accessor')
        if instance and instance.id:
            self.fields['target'].choices = [
                (str(Uri.objects.filter(entity=getattr(instance, self.rel_accessor[2]))[0]),
                 str(getattr(instance, self.rel_accessor[2])))]
            self.fields['target'].initial = (str(Uri.objects.filter(entity=getattr(instance, self.rel_accessor[2]))[0]),
                                             str(getattr(instance, self.rel_accessor[2])))
            if self.rel_accessor[1]:
                self.fields['relation_type'].choices = [(instance.relation_type.id,
                                                         instance.relation_type.label)]
                self.fields['relation_type'].initial = (
                    instance.relation_type.id, instance.relation_type.label)
            else:
                self.fields['relation_type'].choices = [(instance.relation_type.id,
                                                         instance.relation_type.label_reverse)]
                self.fields['relation_type'].initial = (
                    instance.relation_type.id, instance.relation_type.label_reverse)
        if highlighter:
            css_notes = 'HL'
            log.warning("highlighter was true")
        else:
            log.warning("highlighter was false")

        if self.relation_form.__name__.lower() == "personinstitution":
            self.fields["write citation"] = forms.BooleanField()
            self.fields["write citation"].initial = True
            self.fields["write citation"].required = False
            self.helper.include_media = False
            self.helper.layout = Layout(
                'relation_type',
                'target',
                'start_date_written',
                'end_date_written',
                'write citation',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="{}_{}_notes_refs".format(self.relation_form.__name__, css_notes))))
        else:
            self.helper.include_media = False
            self.helper.layout = Layout(
                'relation_type',
                'target',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="{}_{}_notes_refs".format(self.relation_form.__name__, css_notes))))

        if highlighter:
            self.fields['HL_start'] = forms.IntegerField(
                widget=forms.HiddenInput)
            self.fields['HL_end'] = forms.IntegerField(
                widget=forms.HiddenInput)
            self.fields['HL_text_id'] = forms.CharField(
                widget=forms.HiddenInput)
            self.helper.layout.extend([
                'HL_start',
                'HL_end',
                'HL_text_id'])

        if instance != None:

            if instance.start_date_written:
                self.fields['start_date_written'].help_text = DateParser.get_date_help_text_from_dates(
                    single_date=instance.start_date,
                    single_start_date=instance.start_start_date,
                    single_end_date=instance.start_end_date,
                    single_date_written=instance.start_date_written,
                )
            else:
                self.fields['start_date_written'].help_text = DateParser.get_date_help_text_default(
                )

            if instance.end_date_written:
                self.fields['end_date_written'].help_text = DateParser.get_date_help_text_from_dates(
                    single_date=instance.end_date,
                    single_start_date=instance.end_start_date,
                    single_end_date=instance.end_end_date,
                    single_date_written=instance.end_date_written,
                )
            else:
                self.fields['end_date_written'].help_text = DateParser.get_date_help_text_default(
                )

        if not instance or not instance.id or instance.id == "None":
            if prefill_inst:
                if self.fields.get("target"):
                    self.fields['target'].choices = [
                        (str(Uri.objects.filter(entity=prefill_inst)[0]),
                         str(prefill_inst))]
                    self.fields['target'].initial = (str(Uri.objects.filter(entity=prefill_inst)[0]),
                                                     str(prefill_inst))
            if prefill_func:
                if self.fields.get("relation_type"):
                    self.fields['relation_type'].choices = [(prefill_func.id,
                                                             prefill_func.label)]
                    self.fields['relation_type'].initial = (
                        prefill_func.id, prefill_func.label)
