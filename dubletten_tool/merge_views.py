from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
# Create your views here.
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
# from .grouping_script_1 import run
from .models import Group, PersonProxy, StatusButtonGroup, StatusButtonProxy, StatusButtonGroupType
import json
from .suggestions import get_levensthein, check_all_names, get_name_suggestions
from .forms import GroupForm, PersonProxyForm
import logging
from .logger import init_logger
from .merge_tables import VorfinListTable
from apis_core.apis_metainfo.models import Collection
import re
# copied over, delete unnecessary parts

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView
from django_tables2 import RequestConfig
from guardian.core import ObjectPermissionChecker
from reversion.models import Version
import importlib

from apis_core.apis_entities.forms import (
    GenericFilterFormHelper,
    NetworkVizFilterForm,
    PersonResolveUriForm,
    GenericEntitiesStanbolForm,
)
from apis_core.apis_entities.models import Place, Person, Institution
from apis_core.apis_entities.tables import get_entities_table

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import AbstractRelation, PersonInstitution, PersonPerson
from apis_core.apis_relations.tables import LabelTableEdit
from apis_core.apis_entities.forms import get_entities_form, FullTextForm, GenericEntitiesStanbolForm
from apis_core.apis_entities.views import get_highlighted_texts
from apis_core.apis_entities.views import set_session_variables
from apis_core.apis_vocabularies.models import TextType

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import select_template
from django.views import View
from django_tables2 import RequestConfig
from django.urls import reverse


from apis_core.apis_vocabularies.models import PersonInstitutionRelation, PersonPersonRelation
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import LabelTableBase
from apis_core.helper_functions.utils import access_for_all
from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_entities.views import get_highlighted_texts
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django_tables2 import RequestConfig
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

if "charts" in settings.INSTALLED_APPS:
    from charts.models import ChartConfig
    from charts.views import create_payload

from apis_core.apis_metainfo.models import Uri, UriCandidate, Text
from apis_core.apis_relations.models import AbstractRelation
from apis_core.helper_functions.RDFParser import RDFParser
from apis_core.helper_functions.stanbolQueries import retrieve_obj
from apis_core.helper_functions.utils import (
    access_for_all,
    access_for_all_function,
    ENTITIES_DEFAULT_COLS,
)
from apis_core.apis_entities.filters import get_list_filter_of_entity
from .merge_functions import write_person_person_rels, MergeGroup, update_merging_collections

from .merge_tables import get_generic_relations_table

from dubletten_tool.src.functions.remerge_single_group import remerge_single_group
from dubletten_tool.tasks import remerge_group_task

if "apis_ampel" in settings.INSTALLED_APPS:
    from apis_ampel.helper_functions import is_ampel_active

from .redis_client import client as RC
from celery.result import AsyncResult
from apis.celery import app as CELERY_APP


class GenericCeleryTaskStatusView(View):

    def post(self, *args, **kwargs):
        task_id = self.request.POST.get("task_id", None)
        if not task_id:
            # TODO: implement error redirect
            print("task id was not given")
            pass

        async_result = AsyncResult(task_id, app=CELERY_APP)

        return JsonResponse({"status": async_result.status, "result": async_result.result})


@method_decorator(login_required, name="dispatch")
class UpdateCollectionsView(View):
    def get(self, request, *args, **kwargs):
        msg = "Update Collections Finished."
        success = True

        try:
            # TODO: make this a celery task also
            update_merging_collections()
        except Exception as e:
            msg = f"Something went wrong:\n{e}"
            success = False

        return JsonResponse({"msg": msg, "success": success})


@method_decorator(login_required, name="dispatch")
class RemergeGroupView(View):

    def post(self, *args, **kwargs):
        # TODO: make this a post request and pass groups_to_delete array as data.
        print("called new remerge. in post request")
        print(self.request.POST)
        g_id = kwargs.get("g_id")
        data = self.request.POST.getlist("data[]")
        if not data:
            print("NO DATA")
            print(data, type(data))

        groups_to_delete = data
        # groups_to_delete = json.loads(data)
        print(groups_to_delete)
        # group = Group.objects.get(id=g_id)
        # TODO: check why vorfins list isn't passed in here.
        task = remerge_group_task.delay(
            g_id, groups_to_delete=groups_to_delete)

        print("------------->>>>>>>>> TASK_ID", task.id)
        result = {
            "msg": f"Task lives in celery now. TASK_ID: {task.id}",
            "task_id": task.id,
            "success": True,
        }

        # return HttpResponse(test)
        return JsonResponse(result)


@method_decorator(login_required, name="dispatch")
class GenericEntitiesDetailView(UserPassesTestMixin, View):

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        return access

    def get(self, request, *args, **kwargs):

        entity = kwargs['entity'].lower()
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        merged_rel = PersonPersonRelation.objects.get(name="data merged from")
        persons_ = [r.related_personB for r in PersonPerson.objects.filter(
            related_personA=instance, relation_type=merged_rel)]

        relations = AbstractRelation.get_relation_classes_of_entity_name(
            entity_name=entity)
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classA().__name__.lower(),
                rel.get_related_entity_classB().__name__.lower()
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            print("relations_table class is:", rel)
            table = get_generic_relations_table(
                relation_class=rel, entity_instance=instance, detail=True)
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter_for_user().filter(
                        Q(**dict_1) | Q(**dict_2))
                else:
                    objects = rel.objects.filter(
                        Q(**dict_1) | Q(**dict_2))
                    if callable(getattr(objects, 'filter_for_user', None)):
                        objects = objects.filter_for_user()
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {'related_' + entity.lower(): instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(
                        request=request).filter_for_user().filter(**dict_1)
                else:
                    objects = rel.objects.filter(**dict_1)
                    if callable(getattr(objects, 'filter_for_user', None)):
                        objects = objects.filter_for_user()
            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={
                          "per_page": 10}).configure(tb_object)
            side_bar.append(
                (title_card, tb_object, ''.join(
                    [x.title() for x in match]), tb_object_open)
            )
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableBase(
            data=object_labels, prefix=entity.title()[:2]+'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        template = select_template([
            'merge/detail_views/entity_detail_generic.html'
        ])
        tei = getattr(settings, "APIS_TEI_TEXTS", [])
        if tei:
            tei = set(tei) & set([x.kind.name for x in instance.text.all()])
        ceteicean_css = getattr(settings, "APIS_CETEICEAN_CSS", None)
        ceteicean_js = getattr(settings, "APIS_CETEICEAN_JS", None)
        openseadragon_js = getattr(settings, "APIS_OSD_JS", None)
        openseadragon_img = getattr(settings, "APIS_OSD_IMG_PREFIX", None)
        iiif_field = getattr(settings, "APIS_IIIF_WORK_KIND", None)
        if iiif_field:
            try:
                if "{}".format(instance.kind) == "{}".format(iiif_field):
                    iiif = True
                else:
                    iiif = False
            except AttributeError:
                iiif = False
        else:
            iiif = False
        iiif_server = getattr(settings, "APIS_IIIF_SERVER", None)
        iiif_info_json = instance.name
        try:
            no_merge_labels = [
                x for x in object_labels if not x.label_type.name.startswith('Legacy')
            ]
        except AttributeError:
            no_merge_labels = []

        nexturl = instance.get_next_url()
        if nexturl:
            nexturl = nexturl.replace("apis/entities", "dubletten"),
        prevurl = instance.get_prev_url()
        if prevurl:
            prevurl = prevurl.replace("apis/entities", "dubletten")

        return HttpResponse(template.render(
            request=request, context={
                'titles': instance.title.all(),
                'persons': persons_,
                'entity_type': entity,
                'object': instance,
                'right_card': side_bar,
                'no_merge_labels': no_merge_labels,
                'object_lables': object_labels,
                'object_texts': object_texts,
                'object_lod': object_lod,
                'tei': tei,
                'ceteicean_css': ceteicean_css,
                'ceteicean_js': ceteicean_js,
                'iiif': iiif,
                'openseadragon_js': openseadragon_js,
                'openseadragon_img': openseadragon_img,
                'iiif_field': iiif_field,
                'iiif_info_json': iiif_info_json,
                'iiif_server': iiif_server,
                'edit_url': instance.get_edit_url().replace("apis/entities", "dubletten"),
                'next_url': nexturl,
                'prev_url': prevurl,
            }
        ))


class GenericListViewNew(UserPassesTestMixin, ExportMixin, SingleTableView):
    formhelper_class = GenericFilterFormHelper
    context_filter_name = "filter"
    paginate_by = 25
    template_name = getattr(
        settings, "APIS_LIST_VIEW_TEMPLATE", "apis:apis_entities/generic_list.html"
    )
    template_name = "merge/generic_list.html"
    # login_url = "/accounts/login/"

    def get_model(self):
        model = ContentType.objects.get(
            app_label__startswith="apis_", model=self.entity.lower()
        ).model_class()
        return model

    def test_func(self):
        access = access_for_all(self, viewtype="list")
        if access:
            self.request = set_session_variables(self.request)
        return access

    def get_queryset(self, **kwargs):
        self.entity = "Person"  # changed for merge
        vorfin = Collection.objects.get(name="Vorfinale Einträge")

        qs = (
            ContentType.objects.get(
                app_label__startswith="apis_", model=self.entity.lower()
            )
            .model_class()
            .objects.filter(collection__in=[vorfin])
        )

        self.filter = get_list_filter_of_entity(self.entity.title())(
            self.request.GET, queryset=qs
        )

        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs

    def get_table(self, **kwargs):
        session = getattr(self.request, "session", False)
        entity = "Person"
        selected_cols = self.request.GET.getlist("columns")
        if session:
            edit_v = self.request.session.get("edit_views", False)

        else:
            edit_v = False
        if "table_fields" in settings.APIS_ENTITIES[entity.title()]:
            default_cols = settings.APIS_ENTITIES[entity.title(
            )]["table_fields"]
        else:
            default_cols = ["name"]
        default_cols = default_cols + selected_cols
        self.table_class = VorfinListTable

        table = super(GenericListViewNew, self).get_table()
        RequestConfig(
            self.request, paginate={"page": 1, "per_page": self.paginate_by}
        ).configure(table)
        return table

    def get_context_data(self, **kwargs):
        model = self.get_model()
        context = super(GenericListViewNew, self).get_context_data()
        context[self.context_filter_name] = self.filter
        context["entity"] = self.entity
        context["app_name"] = "apis_entities"
        entity = self.entity.title()
        context["entity_create_stanbol"] = GenericEntitiesStanbolForm(
            self.entity)
        if "browsing" in settings.INSTALLED_APPS:
            from browsing.models import BrowsConf

            context["conf_items"] = list(
                BrowsConf.objects.filter(model_name=self.entity).values_list(
                    "field_path", "label"
                )
            )
        context["docstring"] = "{}".format(model.__doc__)
        if model._meta.verbose_name_plural:
            context["class_name"] = "{}".format(
                model._meta.verbose_name.title())
        else:
            if model.__name__.endswith("s"):
                context["class_name"] = "{}".format(model.__name__)
            else:
                context["class_name"] = "{}s".format(model.__name__)
        try:
            context["get_arche_dump"] = model.get_arche_dump()
        except AttributeError:
            context["get_arche_dump"] = None
        try:
            context["create_view_link"] = model.get_createview_url()
        except AttributeError:
            context["create_view_link"] = None
        if "charts" in settings.INSTALLED_APPS:
            app_label = model._meta.app_label
            filtered_objs = ChartConfig.objects.filter(
                model_name=model.__name__.lower(), app_name=app_label
            )
            context["vis_list"] = filtered_objs
            context["property_name"] = self.request.GET.get("property")
            context["charttype"] = self.request.GET.get("charttype")
            if context["charttype"] and context["property_name"]:
                qs = self.get_queryset()
                chartdata = create_payload(
                    context["entity"],
                    context["property_name"],
                    context["charttype"],
                    qs,
                    app_label=app_label,
                )
                context = dict(context, **chartdata)
        try:
            context["enable_merge"] = settings.APIS_ENTITIES[entity.title()
                                                             ]["merge"]
        except KeyError:
            context["enable_merge"] = False
        try:
            togg_cols = settings.APIS_ENTITIES[entity.title(
            )]["additional_cols"]
        except KeyError:
            togg_cols = []
        if context["enable_merge"] and self.request.user.is_authenticated:
            togg_cols = togg_cols + ["merge"]
        context["togglable_colums"] = togg_cols + ENTITIES_DEFAULT_COLS

        return context

    def render_to_response(self, context, **kwargs):
        download = self.request.GET.get("sep", None)
        if download and "browsing" in settings.INSTALLED_APPS:
            import datetime
            import time
            import pandas as pd

            sep = self.request.GET.get("sep", ",")
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime(
                "%Y-%m-%d-%H-%M-%S"
            )
            filename = "export_{}".format(timestamp)
            response = HttpResponse(content_type="text/csv")
            if context["conf_items"]:
                conf_items = context["conf_items"]
                try:
                    df = pd.DataFrame(
                        list(
                            self.get_queryset().values_list(
                                *[x[0] for x in conf_items])
                        ),
                        columns=[x[1] for x in conf_items],
                    )
                except AssertionError:
                    response[
                        "Content-Disposition"
                    ] = 'attachment; filename="{}.csv"'.format(filename)
                    return response
            else:
                response[
                    "Content-Disposition"
                ] = 'attachment; filename="{}.csv"'.format(filename)
                return response
            if sep == "comma":
                df.to_csv(response, sep=",", index=False)
            elif sep == "semicolon":
                df.to_csv(response, sep=";", index=False)
            elif sep == "tab":
                df.to_csv(response, sep="\t", index=False)
            else:
                df.to_csv(response, sep=",", index=False)
            response["Content-Disposition"] = 'attachment; filename="{}.csv"'.format(
                filename
            )
            return response
        else:
            response = super(GenericListViewNew,
                             self).render_to_response(context)
            return response


@method_decorator(login_required, name='dispatch')
class GenericEntitiesEditView(View):

    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        merged_rel = PersonPersonRelation.objects.get(name="data merged from")
        persons_ = [r.related_personB for r in PersonPerson.objects.filter(
            related_personA=instance, relation_type=merged_rel)]
        request = set_session_variables(request)
        relations = AbstractRelation.get_relation_classes_of_entity_name(
            entity_name=entity)
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classA().__name__.lower(),
                rel.get_related_entity_classB().__name__.lower()
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(
                relation_class=rel, entity_instance=instance, detail=False)
            title_card = ''
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter(
                        Q(**dict_1) | Q(**dict_2))
                else:
                    objects = rel.objects.filter(
                        Q(**dict_1) | Q(**dict_2))
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {'related_' + entity.lower(): instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(
                        request=request).filter(**dict_1)
                else:
                    objects = rel.objects.filter(**dict_1)
            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={
                          "per_page": 10}).configure(tb_object)
            side_bar.append((title_card, tb_object, ''.join(
                [x.title() for x in match]), tb_object_open))
        form = get_entities_form(entity.title())
        form = form(instance=instance)
        form_text = FullTextForm(entity=entity.title(), instance=instance)
        if 'apis_highlighter' in settings.INSTALLED_APPS:
            form_ann_agreement = SelectAnnotatorAgreement()
        else:
            form_ann_agreement = False
        if 'apis_bibsonomy' in settings.INSTALLED_APPS:
            apis_bibsonomy = getattr(
                settings, 'APIS_BIBSONOMY_FIELDS', ['self'])
            apis_bibsonomy_texts = getattr(
                settings, "APIS_BIBSONOMY_TEXTS", False)
            if apis_bibsonomy_texts:
                apis_bibsonomy.extend([f"text_{pk}" for pk in TextType.objects.filter(
                    name__in=apis_bibsonomy_texts).values_list('pk', flat=True) if f"text_{pk}" not in apis_bibsonomy])
            if isinstance(apis_bibsonomy, list):
                apis_bibsonomy = '|'.join([x.strip() for x in apis_bibsonomy])
        else:
            apis_bibsonomy = False
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableEdit(
            data=object_labels, prefix=entity.title()[:2] + 'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        perm = ObjectPermissionChecker(request.user)
        permissions = {'change': perm.has_perm('change_{}'.format(entity), instance),
                       'delete': perm.has_perm('delete_{}'.format(entity), instance),
                       'create': request.user.has_perm('entities.add_{}'.format(entity))}
        template = select_template(["merge/entity_create_generic.html"])

        context = {
            'entity_type': entity,
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_card': side_bar,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'object_lod': object_lod,
            'ann_proj_form': ann_proj_form,
            'form_ann_agreement': form_ann_agreement,
            'apis_bibsonomy': apis_bibsonomy,
            'permissions': permissions,
            'detail_url': instance.get_absolute_url().replace("apis/entities", "dubletten")
        }
        form_merge_with = GenericEntitiesStanbolForm(entity, ent_merge_pk=pk)
        context['form_merge_with'] = form_merge_with
        if "apis_ampel" in settings.INSTALLED_APPS:
            context["show_ampel"] = is_ampel_active(entity)
        return HttpResponse(template.render(request=request, context=context))

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        form = get_entities_form(entity.title())
        form = form(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
            return redirect(reverse('dubletten_tool:generic_entities_edit_view', kwargs={
                'pk': pk, 'entity': entity
            }))
        else:
            template = select_template(["merge/entity_create_generic.html"])

            perm = ObjectPermissionChecker(request.user)
            permissions = {'change': perm.has_perm('change_{}'.format(entity), instance),
                           'delete': perm.has_perm('delete_{}'.format(entity), instance),
                           'create': request.user.has_perm('entities.add_{}'.format(entity))}
            context = {
                'form': form,
                'entity_type': entity,
                'form_text': form_text,
                'instance': instance,
                'permissions': permissions}
            if entity.lower() != 'place':
                form_merge_with = GenericEntitiesStanbolForm(
                    entity, ent_merge_pk=pk)
                context['form_merge_with'] = form_merge_with
                return TemplateResponse(request, template, context=context)
            return HttpResponse(template.render(request=request, context=context))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesCreateView(View):
    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        form = get_entities_form(entity.title())
        form = form()
        form_text = FullTextForm(entity=entity.title())
        permissions = {'create': request.user.has_perm(
            'entities.add_{}'.format(entity))}
        template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                    'apis_entities/entity_create_generic.html'])
        return HttpResponse(template.render(request=request, context={
            'entity_type': entity,
            'permissions': permissions,
            'form': form,
            'form_text': form_text}))

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        form = get_entities_form(entity.title())
        form = form(request.POST)
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
            return redirect(reverse('apis:apis_entities:generic_entities_detail_view', kwargs={
                'pk': entity_2.pk, 'entity': entity
            }))
        else:
            permissions = {'create': request.user.has_perm(
                'apis_entities.add_{}'.format(entity))}
            template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                        'apis_entities/entity_create_generic.html'])
            return HttpResponse(template.render(request=request, context={
                'permissions': permissions,
                'form': form,
                'form_text': form_text}))


def getRelationsHelperFunction(instance):
    rels = instance.personinstitution_set.values("id", "related_institution", "related_institution__name",
                                                 "relation_type", "relation_type__name", "start_date_written", "end_date_written")
    rels = sorted(rels, key=lambda k: (k["relation_type__name"], k["related_institution__name"], (
        "1400" if not k["start_date_written"] else k["start_date_written"])), reverse=True)
    [el.update({"include": True}) for el in rels]
    return rels


@method_decorator(login_required, name="dispatch")
class GetRelationEditor(TemplateView):
    template_name = "merge/relation_editor.html"

    def get_context_data(self, **kwargs):
        inst = Person.objects.get(id=self.kwargs.get("pk"))
        merged_rel = PersonPersonRelation.objects.get(name="data merged from")
        persons = [r.related_personB for r in PersonPerson.objects.filter(
            related_personA=inst, relation_type=merged_rel)]
        edit_url = inst.get_edit_url().replace("apis/entities", "dubletten")
        detail_url = inst.get_absolute_url().replace("apis/entities", "dubletten")

        rels = getRelationsHelperFunction(inst)
        rels = json.dumps(rels)
        print(rels)
        return {"test": 20, "relations": rels, "detail_url": detail_url, "edit_url": edit_url, "instance": json.dumps({"name": f"{inst.name}, {inst.first_name}", "id": inst.id}), "object": inst, "persons": persons}


@method_decorator(login_required, name="dispatch")
class DeleteRelation(View):

    def dispatch(self, request, **kwargs):
        msg = "success"
        success = True
        try:
            rel_id = kwargs.get("rel_id")
            rel = PersonInstitution.objects.get(id=rel_id)
            rel.delete()
        except Exception as e:
            msg = f"Something went wrong: {e}"
            success = False

        return JsonResponse({"msg": msg, "success": success})


@method_decorator(login_required, name="dispatch")
class CreateRelationView(View):
    # todo: check that this is failsave
    def post(self, request):
        success = True
        msg = True
        re_id = None
        per = get_object_or_404(Person, pk=request.POST.get(
            "id", "-111"))  # todo: check if this is best solution
        data = json.loads(request.POST.get("relation"))
        del data["id"]
        try:
            temp = {}
            temp.update({"related_person": per})
            temp.update({"related_institution": Institution.objects.get(
                id=data["related_institution"])})
            temp.update({"relation_type": PersonInstitutionRelation.objects.get(
                id=data["relation_type"])})
            rel = PersonInstitution.objects.create(**temp)
            rel.save()
        except Exception as e:
            success = False
            msg = f"Couldn't create new Relation:\n {e}"

        return JsonResponse({"success": success, "msg": msg, "rel_id": rel.id})


@method_decorator(login_required, name="dispatch")
class UpdateFieldView(View):
    def post(self, request):
        success = True
        msg = "success"

        data = json.loads(request.POST.get("relation"))
        field_name = request.POST.get("field_name")
        rel = get_object_or_404(PersonInstitution, pk=data["id"])
        try:

            # todo: convert year only to add 06-30 automatically
            if field_name in ["start_date_written", "end_date_written"] and re.match(r"\d{4}", data[field_name].strip()[-4:]) and not "/" in data[field_name]:
                print("date matched", data[field_name])
                data[field_name] = f"{data[field_name]}<{data[field_name].strip()[-4:]}-06-30>"
                print("changed data field name to:", data[field_name])
            elif field_name in ["start_date_written", "end_date_written"] and re.match(r"\d{4}-\d{2}-\d{2}", data[field_name].strip()[-10:]) and not "<" in data[field_name] and not ">" in data[field_name] and not "/" in data[field_name]:
                data[field_name] = f"{data[field_name]}<{data[field_name].strip()[-10:]}>"
                print("caught long date without <")
            else:
                print("date didn't match", data[field_name])
            setattr(rel, field_name, data[field_name])
            rel.save()
            field_value = data[field_name]
        except Exception as e:
            success = False
            msg = f"Couldn't save field:\n{e}"
            field_value = False

        return JsonResponse({"success": success, "msg": msg, "new_value": field_value})
