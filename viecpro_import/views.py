import sys
import re
import json
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django_tables2 import RequestConfig
from guardian.core import ObjectPermissionChecker

from apis_core.apis_entities.forms import FullTextForm
from apis_core.apis_entities.models import AbstractEntity, Event, Institution, Person, Place, Work
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import LabelTableEdit
from apis_core.apis_relations.views import registered_forms, form_class_dict
from apis_core.apis_vocabularies.models import AbstractRelationType, VocabsBaseClass
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri, Collection
from apis_core.helper_functions.utils import (
    access_for_all_function,
)
from .tables import get_generic_entity_progress_table, get_generic_relation_progress_table, \
    get_generic_relations_table, \
    EntityUriTable
from .forms import get_custom_generic_entities_form,  \
    get_generic_entity_type_form, get_generic_vocabs_form, get_generic_relationtype_form, get_subclass_dic, \
    CustomGenericRelationForm, UploadFileForm, \
    CreateImportProjectForm, EditDataSourceForm
from .models import DataSourceProjectState, DataSource, ImportProject, PageData, ProjectState
from .serializers import EntitySerializer
from .upload_helper import create_datasource_and_pages, update_datasource_and_pages

# if 'apis_highlighter' in settings.INSTALLED_APPS:
#     from apis_core.helper_functions.highlighter import highlight_text
#     from apis_highlighter import forms as highlighter_form_module
#
#     form_module_list.append(highlighter_form_module)


# NOTE: log level is set in .logger.py. Set level to INFO for stdout-logstreams
log = logging.getLogger("mylogger")


# todo: __refactor__ __gpirgie__ move helper functions to seperate file

def get_json_rel(rel_class=None, rel_id=None, instance=None, version="-"):
    if not instance:
        model = AbstractRelation.get_relation_class_of_name(rel_class)
        rel = model.objects.get(id=rel_id)
    else:
        rel = instance

    data = {}
    instA = rel.get_related_entity_instanceA()
    instB = rel.get_related_entity_instanceB()
    classA = rel.get_related_entity_classA()
    classB = rel.get_related_entity_classB()

    data["start_date_written"] = rel.start_date_written
    data["end_date_written"] = rel.end_date_written
    data["relation_type"] = {
        "name": rel.relation_type.name,
        "id": rel.relation_type.id,
        "class": rel.__class__.__name__
    }
    data["relation_source"] = {
        "name": str(instA),
        "id": instA.id,
        "class": classA.__name__
    }
    data["relation_target"] = {
        "name": str(instB),
        "id": instB.id,
        "class": classB.__name__
    }
    data["version"] = version  # todo: check that this is implemented throughout

    for k, v in data.items():
        if not v:
            data[k] = ""

    return data


# todo: __feature__ __gpirgie__ consider implementing a seperate searialization, and table for labels; with
#  labeltype, sdw, edw, and entity.
def get_json_entity(entity, version="-"):
    # todo: __gpirgie__ instead of showing all data, it might be more reasonable to show the differences to the
    #  last version and display that in the frontend
    apis_serialization = EntitySerializer(entity).data
    # apis_serialization = entity.get_serialization()

    if apis_serialization["entity_type"] == "Person":
        titles = [t.name for t in entity.title.all()]
    else:
        titles = None
    labels = [l.label for l in entity.label_set.all()]
    data = {key: value for key, value in apis_serialization.items() if key in [
        "id",
        "name",
        "first_name",
        "start_date_written",
        "end_date_written",
        "entity_type",
        "gender"]
            }
    data["version"] = version
    data["labels"] = labels
    if apis_serialization["entity_type"] == "Person":
        data["titles"] = titles
    if "kind" in apis_serialization.keys():
        kind = apis_serialization.get("kind")
        if kind:
            data["kind"] = kind.get("label")
        else:
            data["kind"] = ""

    for k, v in data.items():
        if not v:
            data[k] = ""

    return data


@user_passes_test(access_for_all_function)
def set_session_variables(request):
    ann_proj_pk = request.GET.get("project", None)
    types = request.GET.getlist("types", None)
    users_show = request.GET.getlist("users_show", None)
    edit_views = request.GET.get("edit_views", False)
    if types:
        request.session["entity_types_highlighter"] = types
    if users_show:
        request.session["users_show_highlighter"] = users_show
    if ann_proj_pk:
        request.session["annotation_project"] = ann_proj_pk
    if edit_views:
        if edit_views != "false":
            request.session["edit_views"] = True
    return request


"""
SESSION_KEYS = [
    "ds_pk",
    "project_pk",
    "page_num",
    "page_id",
    "col_pk",
    "datasource",
    "project",
    "pagedata",
    "year",
    "citation",
    "ent_pk",
    "ent_type",
    "pagedata_pk",
]
"""



@login_required()
def update_datasource_select_ajax(request):
    html = update_datasource_select(request)
    return JsonResponse({"select_html": html})


def update_datasource_select(request):
    template = "element_templates/element_datasources_select_template.html"
    project_pk = request.session.get("project_pk")
    project = ImportProject.objects.get(pk=project_pk)
    data_sources = list(project.DataSources.all())

    if request.method == "POST":
        ds_pk = request.POST.get("ds_pk")
        # request.session["ds_pk"] = ds_pk # todo: check if this works, changed this by adding this line
        last_ds = DataSource.objects.get(id=ds_pk)
        data_sources.remove(last_ds)
    else:
        user = request.user
        project_state, c = ProjectState.objects.get_or_create(project=project, user=user)
        last_ds = project_state.last_datasource

        if not last_ds and data_sources:
            last_ds = data_sources.pop(0)
        elif data_sources and last_ds not in data_sources:
            project_state.last_datasource = data_sources[0]
            project_state.save()
        elif data_sources:
            data_sources.remove(last_ds)

    return render_to_string(template, {"DataSources": data_sources, "last_ds": last_ds}, request)


# Form Handling
@login_required()
def update_datasource(request):
    template = "element_templates/element_datasource_update.html"
    ds_pk = request.session.get("ds_pk")
    instance = DataSource.objects.get(id=ds_pk)

    if request.method == "POST":
        form = EditDataSourceForm(data=request.POST, instance=instance)

        if form.is_valid():
            ds = form.save()
            update_datasource_and_pages(ds)

            return JsonResponse({"success": "true", "msg": f"Updated {ds.name}", "ds_pk": ds_pk})
        else:
            return JsonResponse({"success": "true", "msg": f"Couldn't update DataSource."})

    else:
        form = EditDataSourceForm(instance=instance)
        data = {"content": render_to_string(template, {"form": form, "ds_name": instance.name}, request)}
        return JsonResponse(data)


@login_required()
def upload_pdf(request, **kwargs):
    project_pk = request.session.get("project_pk")

    template = "element_templates/element_datasources_upload.html"
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES, project_pk=project_pk)

        context_dict = {}

        if form.is_valid():

            ds_pk = create_datasource_and_pages(request)
            context_dict["success"] = True

            context_dict["ds_pk"] = ds_pk
            return JsonResponse(context_dict)
        else:
            context_dict["success"] = False
            HttpResponse(json.dumps(context_dict), mimeType="application/json")

    else:
        form = UploadFileForm(project_pk=project_pk)

        data = {"content": render_to_string(template, {"form": form}, request)}
        return JsonResponse(data)


@login_required()
def create_import_project(request, **kwargs):
    template = "element_templates/element_project_create.html"
    action = "Create"
    if request.method == "POST":
        form = CreateImportProjectForm(request.user, request.POST)
        form.helper.form_action = reverse("viecpro_import:project_create")

        if form.is_valid():
            user = request.user
            pi = form.save()
            pi.Editors.add(user)
            pi.save()

            return redirect(reverse("viecpro_import:project_main"))

    else:
        form = CreateImportProjectForm(user=request.user)
        form.helper.form_action = reverse("viecpro_import:project_create")
        data = {"content": render_to_string(template, {"form": form, "action": action}, request)}
        return JsonResponse(data)


@login_required
def edit_import_project(request, **kwargs):
    pk = kwargs.get("project_pk")
    instance = ImportProject.objects.get(pk=int(pk))
    template = "element_templates/element_project_create.html"
    action = "Update"

    if request.method == "POST":
        form = CreateImportProjectForm(request.user, request.POST, instance=instance)
        form.helper.form_action = reverse("viecpro_import:project_update", kwargs={"project_pk": pk})

        if form.is_valid():
            user = request.user
            pi = form.save()
            if user not in pi.Editors.all():
                pi.Editors.add(user)

            pi.save()

            return redirect(reverse("viecpro_import:project_main"))


    else:
        form = CreateImportProjectForm(user=request.user, instance=instance)
        form.helper.form_action = reverse("viecpro_import:project_update", kwargs={"project_pk": pk})

        data = {"content": render_to_string(template, {"form": form, "action": action}, request)}
        return JsonResponse(data)


def clear_session_data(request_):
    keys = ["page_num", "year", "citation", "col_pk", "pagedata_pk", "ds_pk", "ent_pk",
            "ent_type"]
    for k in keys:
        request_.session[k] = None


@method_decorator(login_required, name='dispatch')
class EditorPageView(TemplateView):
    template_name = "pages/editor_page.html"

    def get_context_data(self, **kwargs):
        project_pk = kwargs.get("project_pk")
        project = ImportProject.objects.get(pk=project_pk)
        self.request.session["project_pk"] = project_pk

        clear_session_data(self.request)

        user = self.request.user
        if user.is_authenticated and user in project.Editors.all():
            ds_select_html = update_datasource_select(self.request)
            context = {"project": project, "ds_select_html": ds_select_html}
            return context
        else:
            return Http404


@method_decorator(login_required, name='dispatch')
class ProjectPageView(TemplateView):
    template_name = "pages/projects_page.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        projects = ImportProject.objects.filter(Editors=user)
        project_tuple = [(pr, pr.get_role(user)) for pr in projects]

        context = {
            "user": user,
            "projects": project_tuple,
        }

        return context


@login_required()
def editor_autocomplete(request, **kwargs):
    entity_type = kwargs.get("entity")
    entity_type = entity_type.lower()
    full_db = kwargs.get("full_db")

    def get_person_entry(p):
        name = str(p)
        if p.start_date:
            birth = p.start_date.strftime("%Y")
        else:
            birth = ""
        if p.end_date:
            death = f"†{p.end_date.strftime('%Y')}"
        else:
            death = ""
        if birth or death:
            name = f"{name} ({birth} {death})"

        return name

    if entity_type == "person":
        if full_db:
            pers = Person.objects.all()
        else:
            col_hsv = Collection.objects.get(name__contains="Import HSV")
            col_hzab = Collection.objects.get(name__contains="Import HZAB")
            pers = Person.objects.exclude(
                    collection__in=[col_hsv,
                                    col_hzab])

        values = [[get_person_entry(a), "person", a.pk] for a in pers if a]
        result = [{"label": v[0], "value": v, "group": v[1], "pk": v[2]} for v in values]

    elif entity_type == "place":
        places = Place.objects.all()
        result = [{"label": el.name, "value": [el.name, "place", el.pk], "pk": el.pk} for el in places]

    elif entity_type == "institution":
        insts = Institution.objects.all()
        result = [{"label": el.name, "value": [el.name, "institution", el.pk], "pk": el.pk} for el in insts]

    elif entity_type == "event":
        events = Event.objects.all()
        result = [{"label": el.name, "value": [el.name, "event", el.pk], "pk": el.pk} for el in events]

    elif entity_type == "work":
        works = Work.objects.all()
        result = [{"label": el.name, "value": [el.name, "work", el.pk], "pk": el.pk} for el in works]

    response_data = {"context": result}

    return JsonResponse(response_data)


def save_to_collection(instance, collection):
    instance.collection.add(collection)
    instance.save()
    log.info(f"updated relation collection: rel is: {instance}, collections is: {instance.collection.all()}")


def save_citation(instance, citation, page_num):
    if citation and page_num:
        cit = f"{citation}, {page_num}."
        notes = instance.notes
        if not notes or not cit in notes:
            if notes:
                instance.notes += f"\n{cit}"
            else:
                instance.notes = cit
            instance.save()
            log.info(f"Saved citation, instance notes are now {instance.notes}")

        else:
            log.info(f"citation was already in notes - {cit}, notes: {notes}")


def set_start_page(request):
    ds = request.session.get("ds_pk")
    page_num = request.session.get("page_num")
    page_token = request.POST.get("page_token")

    log.info(f"ds = {ds}, page_num = {page_num}, page_token = {page_token}")
    res = reset_page_tokens(ds, page_num, page_token)

    if res:
        return JsonResponse(
                {"success": True, "msg": f"Set page numbers starting from page_index {page_num} to {page_token}"})


def reset_page_tokens(ds_pk, page, token):
    ds = DataSource.objects.get(id=ds_pk)
    ds.set_start_page(page_num=page, page_token=token)

    return True


def get_pagedata_obj(request):
    ds_pk = request.session.get("ds_pk")
    ds = DataSource.objects.get(id=ds_pk)
    page = ds.get_page_object(page_num=request.session.get("page_num"))
    project_pk = request.session.get("project_pk")
    project = ImportProject.objects.get(id=project_pk)
    pagedata = project.pagedata_set.get(page=page)
    return pagedata


def save_to_edited(request, obj, project, serialization=None):
    pagedata = PageData.objects.get(id=request.session.get("pagedata_pk"))

    if not pagedata.get_created():
        pagedata.add_to_edited(obj, serialization, project=project)
        log.info(f"saved {obj} to collection edited")

    elif obj not in pagedata.get_created():
        pagedata.add_to_edited(obj, serialization, project=project)
        log.info(f"saved {obj} to collection edited")

    else:
        log.info(f"{obj} was in collection created, no action taken")


def save_to_created(request, object):
    pagedata = PageData.objects.get(id=request.session.get("pagedata_pk"))
    pagedata.add_to_created(object)
    log.info(f"saved {object} to created")


@login_required()
def editor_session_update(request):
    ent_type = request.POST.get("ent_type")
    ent_pk = request.POST.get("ent_pk")
    request.session["ent_type"] = ent_type
    request.session["ent_pk"] = ent_pk
    log.info(f"set ent_type {ent_type} and ent_pk {ent_pk}")

    return JsonResponse({"success": True})


@login_required()
def ds_select_post(request, **kwargs):
    first_call = request.POST.get("first_call")
    log.info(f"first call: {first_call}")
    user = request.user
    project_pk = request.session.get("project_pk")
    project = ImportProject.objects.get(id=project_pk)

    if first_call == "false":
        ds_pk = request.POST.get("ds_pk")
        log.info(f"ds_pk set to: {ds_pk}")
        ds = DataSource.objects.get(id=ds_pk)
        request.session["ds_pk"] = ds_pk
        ds_state, c = ProjectState.objects.get_or_create(user=user, project=project)
        ds_state.last_datasource = ds
        ds_state.save()
    elif first_call == "true":
        # if page gets reloaded, fetch last datasource from project
        ds_state, c = ProjectState.objects.get_or_create(user=user, project=project)
        ds = ds_state.last_datasource
        log.info(f"last datasource in {project} is {ds}")
        if not ds:
            ds_set = project.DataSources.all()

            ds = ds_set[0]

        request.session["ds_pk"] = ds.pk

    ds_state_p, c = DataSourceProjectState.objects.get_or_create(datasource=ds, user=user, project=project)
    last_page = ds_state_p.last_page

    if last_page:
        request.session["page_num"] = last_page.page_index
    else:
        request.session["page_num"] = 1

    return JsonResponse({"success": True})


@login_required()
def update_browser(request):
    year = citation = page_data_obj = project_col = img_path = page_count = page_token = name = None

    project_pk = request.session.get("project_pk")  # session varibale is set on page load
    project = ImportProject.objects.get(id=project_pk)
    log.info(f"project_pk is {project_pk}")

    page_num = request.POST.get("page_num")
    direction = request.POST.get("direction")

    if not page_num:
        page_num = request.session.get("page_num")
        if not page_num:
            page_num = 1

    page_num = int(page_num)
    if direction:
        if direction == "next":
            page_num += 1
        elif direction == "prev":
            page_num -= 1

    ds_pk = request.session.get("ds_pk")  # session variable is set on page load
    log.info(f"ds_pk is {ds_pk}")
    # implement check if page is in page range of datasource
    if ds_pk:
        ds = DataSource.objects.get(id=int(ds_pk))
        page_count = ds.page_count
        if page_num > page_count:
            page_num = page_count
        elif page_num < 1:
            page_num = 1
        name = ds.name
        img_path = ds.get_page_url(page_num)
        page_obj = ds.get_page_object(page_num)
        year = ds.year
        citation = ds.citation
        page_token = page_obj.page_token
        try:
            page_data_obj, created = PageData.objects.get_or_create(project=project, page=page_obj)
        except MultipleObjectsReturned as e:
            log.info(f"intercepted {e}")
            multiples = list(PageData.objects.filter(project=project, page=page_obj))
            page_data_obj = multiples.pop(0)
            [el.delete() for el in multiples]

    else:
        log.info("ds_pk was false")

    project_col = project.collection

    template = "section_templates/datasource_browser.html"

    if page_num:
        request.session["page_num"] = page_num
    if year:
        request.session["year"] = year
    if citation:
        request.session["citation"] = citation
    if project_col:
        request.session["col_pk"] = project_col.id
    if page_data_obj:
        request.session["pagedata_pk"] = page_data_obj.id

    user = request.user

    if ds_pk:
        ds_state, c = DataSourceProjectState.objects.get_or_create(datasource=ds, user=user, project=project)
        ds_state.last_page = page_obj
        ds_state.save()

    context = {
        "page_num": page_num,
        "data_source_pk": ds_pk,
        "img_path": img_path,
        "name": name,
        "year": year,
        "page_token": page_token,
        "page_count": page_count,
        "citation": citation,
    }

    html = {"browser_html": render_to_string(template, context, request)}

    return JsonResponse(html)


def get_relation_section_html(request):
    pass


def get_metadata_section_html(request):
    pass


def get_itemcreate_section_html(request):
    test_template = "section_templates/generic_create_items_section.html"

    entities_ = [(a, a.capitalize()) for a in AbstractEntity.get_all_entity_names()]
    entity_names = [(a.capitalize(), a) for a in AbstractEntity.get_all_entity_names()]

    def cap(x):
        for l, u in entities_:
            x = x.replace(l, u)

        x = x.replace("relation", "Relation")
        return x

    relation_types = [cap(r) for r in AbstractRelationType.get_all_relationtype_names()]
    relation_types = [(rt, get_generic_relationtype_form(rt)()) for rt in relation_types]
    entity_types = [(et, get_generic_entity_type_form(et)()) for et in
                    ["InstitutionType", "EventType", "PlaceType", "WorkType"]]

    title_form = get_generic_vocabs_form("Title")()
    label_form = get_generic_vocabs_form("LabelType")()

    context_test_html = {
        'APPS': settings.INSTALLED_APPS,
        'relation_types': relation_types,
        'entities_': entity_names,
        'entity_types': entity_types,
        'title_form': title_form,
        'label_form': label_form,
    }

    return render_to_string(test_template, context_test_html, request)


def get_pageprocess_section_html(request):
    log.info("called")
    session_ = request.session
    process_template = "section_templates/generic_process_section.html"
    ds_pk = session_.get("ds_pk")
    ds = DataSource.objects.get(id=ds_pk)
    page = ds.get_page_object(session_.get("page_num"))
    project_pk = session_.get("project_pk")
    project = ImportProject.objects.get(id=project_pk)
    pagedata = page.get_pagedata(project=project)

    # todo: need to place this somewhere else, to delete non values from pagedata objects, as they result in display
    #  issues

    # [el.delete() for el in pagedata.get_all() if el.content_object == None]
    log.info(f"Cleared None values from pagedata")
    edited = pagedata.get_edited_dict_named_with_version(project=project)
    created = pagedata.get_created_dict_named()

    template_edited = "section_templates/progress_edited_template.html"
    template_created = "section_templates/progress_created_template.html"
    template_deleted = "section_templates/progress_deleted_template.html"
    context_edited = {}
    context_created = {}
    context_deleted = {}

    if edited:
        items_edited = edited.items()
        edited_relations = []
        edited_entities = []
        edited_other = []

        for key, values in items_edited:
            test = False
            for v in values:
                if v[0]:
                    test = True
            if not test:
                continue

            if key in settings.APIS_ENTITIES.keys():
                new_values = []
                for v in values:           
                    new_values.append(get_json_entity(v[0]))
                    if not "version" in v[1].keys():
                        v[1]["version"] = "original"
                        log.info(f"v1 is now {v[1]}")
                    new_values.append(v[1])

                temp_table = get_generic_entity_progress_table(data=new_values)
                edited_entities.append((key, temp_table))

            elif key in list(filter(lambda x: re.match(r"[A-Z]", x), settings.APIS_RELATIONS.keys())):

                new_values = []
                for v in values:
                    if not v[0]:
                        continue
                    log.info(f"v0 is {v[0]}, key is {key}, v0type is {type(v[0])}")
                    new_values.append(get_json_rel(rel_class=key, rel_id=v[0].id))
                    if not "version" in v[1].keys():
                        v[1]["version"] = "original"
                        log.info(f"v1 is now {v[1]}")
                    new_values.append(v[1])

                temp_table = get_generic_relation_progress_table(data=new_values)
                edited_relations.append((key, temp_table))

            else:
                edited_other.append((key, values))

        context_edited["edited_relations"] = edited_relations
        context_edited["edited_entities"] = edited_entities
        context_edited["edited_other"] = edited_other
        edited_html = render_to_string(template_edited, context_edited, request)

    else:
        edited_html = None
    if created:
        items_created = created.items()

        created_entities = []
        created_relations = []
        created_other = []

        for key, values in items_created:
            test = False
            for v in values:
                if v:
                    test = True
            if not test:
                continue
            if key in settings.APIS_ENTITIES.keys():
                new_values = [get_json_entity(v) for v in values if v]
                table = get_generic_entity_progress_table(data=new_values, version=False)
                created_entities.append((key, table))

            elif key in list(filter(lambda x: re.match(r"[A-Z]", x), settings.APIS_RELATIONS.keys())):
                log.info(f"key is: {key}")
                new_values = [get_json_rel(instance=v) for v in values if v]
                table = get_generic_relation_progress_table(data=new_values, version=False)
                created_relations.append((key, table))

            else:
                created_other.append((key, values))


        context_created["created_entities"] = created_entities
        context_created["created_relations"] = created_relations
        context_created["created_other"] = created_other
        context_created["items_created"] = [(key, value) for key, value in items_created]
        created_html = render_to_string(template_created, context_created, request)


    else:
        context_created["items_created"] = []
        created_html = None

    deleted_html = render_to_string(template_deleted, context_deleted, request)

    html_cont = render_to_string(process_template, {
        "edited_html": edited_html, "created_html": created_html, "deleted_html": deleted_html
    }, request)

    return html_cont


def editor_update_section(request, **kwargs):
    log.info("called")
    section = kwargs.get("section")
    section_dic = {
        "itemcreate": get_itemcreate_section_html,
        # "create":get_create_section_html,
        "pageprocess": get_pageprocess_section_html,
    }
    html = section_dic[section](request)

    return JsonResponse({"content": {section: html}})


@method_decorator(login_required, name="dispatch")
class EditorAllSectionsView(View):

    def get(self, *args, **kwargs):
        session_ = self.request.session
        entity = session_['ent_type']
        pk = session_['ent_pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        request = set_session_variables(self.request)
        relations = AbstractRelation.get_relation_classes_of_entity_name(entity_name=entity)
        form_text = FullTextForm(entity=entity.title(), instance=instance)

        # relations = relations[:-1]
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classA().__name__.lower(),
                rel.get_related_entity_classB().__name__.lower()
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(relation_class=rel, entity_instance=instance, detail=False)
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

                # removed apis_highlighter if clause here.
                objects = rel.objects.filter(**dict_1)

            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={"per_page": 1000}).configure(
                    # todo: __refactor__ IMPORTANT __gpirgie__ disabled pagination, as I didn't have the time to
                    #  implement it correctly. For entities with a lot of relations, this causes delaus in loading them.
                        # fixme: __maintainence__ __gpirgie__ implement pagination via ajax

                    tb_object)
            side_bar.append((title_card, tb_object, ''.join([x.title() for x in match]), tb_object_open))
        form = get_custom_generic_entities_form(entity.title())
        form = form(instance=instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        object_lod = Uri.objects.filter(entity=instance)

        tb_label = LabelTableEdit(data=object_labels, prefix=entity.title()[:2] + 'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        perm = ObjectPermissionChecker(request.user)
        permissions = {
            'change': perm.has_perm('change_{}'.format(entity), instance),
            'delete': perm.has_perm('delete_{}'.format(entity), instance),
            'create': request.user.has_perm('entities.add_{}'.format(entity))
        }
        rel_template = "section_templates/generic_relations_section.html"
        meta_template = "section_templates/generic_entity_meta_section.html"
        # test_template = "section_templates/generic_create_items_section.html"

        context = {
            'entity_type': entity,
            'is_create': False,
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_card': side_bar,
            # 'object_revisions': object_revisions,
            # 'object_texts': object_texts,
            'object_lod': object_lod,
            # 'ann_proj_form': ann_proj_form,
            # 'form_ann_agreement': form_ann_agreement,
            # 'apis_bibsonomy': apis_bibsonomy,
            'permissions': permissions
        }

        html_rel = render_to_string(rel_template, context, request)
        html_meta = render_to_string(meta_template, context, request)

        if entity.lower() == "person":
            ent_name = f"{instance.name}, {instance.first_name}"
        else:
            ent_name = instance.name
        return JsonResponse({
            "content": {
                "ent_name": ent_name,
                "relations_html": html_rel, "meta_html": html_meta  # "test_html": html_test,
                # "control_html": html_cont
            }, "entity_type": entity,
        })

    def post(self, *args, **kwargs):
        pass


@login_required()
def update_control_section(request):  # todo: __refactor__ __gpirgie__ rename to pageprocess
    session_ = request.session
    control_template = "section_templates/generic_process_section.html"
    ds_pk = session_.get("ds_pk")
    ds = DataSource.objects.get(id=ds_pk)
    page = ds.get_page_object(session_.get("page_num"))
    project_pk = session_.get("project_pk")
    project = ImportProject.objects.get(id=project_pk)
    pagedata = page.get_pagedata(project=project)
    res = pagedata.get_edited_dict_named()
    if res:
        items = res.items()
        context_cont = {"items": [(key, value) for key, value in items]}
    else:
        context_cont = {"items": []}

    html_cont = render_to_string(control_template, context_cont, request)

    return JsonResponse({
        "content": {
            "control_html": html_cont
        }
    })


@method_decorator(login_required, name='dispatch')
class GenericEntitiesUpdateView(View):
    # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function if possible

    def get_html_str(self, *args, **kwargs):
        log.info("CALLED THIS")

        entity = kwargs['entity']
        form = get_custom_generic_entities_form(entity.title())
        form = form()

        form_text = FullTextForm(entity=entity.title())
        permissions = {'create': self.request.user.has_perm('entities.add_{}'.format(entity))}
        template = "section_templates/generic_entity_meta_section.html"

        context = {
            'entity_type': entity,
            'is_create': False,
            'permissions': permissions,
            'form': form,
            'form_text': form_text,
            'is_create': True
        }
        html_str = render_to_string(template, context, self.request)
        return html_str

    def get(self, *args, **kwargs):
        html = self.get_html_str(*args, **kwargs)

        return JsonResponse({"content": html})

    def post(self, *args, **kwargs):
        log.info("CALLED THIS")

        entity = kwargs['entity']
        pk = kwargs['pk']
        project_pk = self.request.session.get("project_pk")
        project = ImportProject.objects.get(pk=project_pk)
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        form = get_custom_generic_entities_form(entity.title())
        form = form(self.request.POST, instance=instance)
        form_text = FullTextForm(self.request.POST, entity=entity.title())
        form_name = f"entity_section_{entity}"
        call_function = "CreateItem_response"
        serialization = get_json_entity(instance)

        if form.is_valid():  # and form_text.is_valid():
            ent = form.save()

            save_to_edited(self.request, ent, project, serialization)
            # form_text.save(ent)
            success = True
            res_msg = f"Updated {entity}-Object {instance}"

        else:
            success = False
            res_msg = f"{entity}-Object  {instance} could not be updated. Please check input."

        return JsonResponse(
                {
                    "call_function": call_function, "msg": res_msg, "form_name": form_name, "success": success,
                    "ent_type": entity, "selected_name": str(ent)
                })


@method_decorator(login_required, name='dispatch')
class GenericEntitiesCreateView(View):
        # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function if possible


    def get_html_str(self, *args, **kwargs):
        entity = kwargs['entity']

        form = get_custom_generic_entities_form(entity.title())
        form = form()

        form_text = FullTextForm(entity=entity.title())
        permissions = {'create': self.request.user.has_perm('entities.add_{}'.format(entity))}
        template = "section_templates/generic_entity_meta_section.html"
        # todo: __refactor__ __gpirgie__ create seperate templates for create and update.

        context = {
            'entity_type': entity,
            # 'is_create': True, # todo: not needed if I use different templates for update and create.
            'permissions': permissions,
            'form': form,
            'form_text': form_text,
            'is_create': True
        }

        html_str = render_to_string(template, context, self.request)

        return html_str

    def get(self, *args, **kwargs):
        html = self.get_html_str(*args, **kwargs)

        return JsonResponse({"content": html})

    def post(self, *args, **kwargs):
        entity = kwargs['entity']
        form = get_custom_generic_entities_form(entity.title())
        form = form(self.request.POST)
        form_text = FullTextForm(self.request.POST, entity=entity.title())
        form_name = f"entity_section_{entity}"
        call_function = "CreateItem_response"
        ent = None
        if form.is_valid():  # and form_text.is_valid():
            # fixme: __gpirgie__ prevents creation of existing entities, but this might not be wanted across all
            #  apis-instances
            name = self.request.POST["name"]
            ent_class = AbstractEntity.get_entity_class_of_name(entity.title())
            #exists_test = ent_class.objects.filter(name=name)
            if ent_class == Person:
                exists_test = False
            else:
                exists_test = ent_class.objects.filter(name=name)
            if exists_test:
                success = False
                res_msg = f"{entity.title()}-Instance with name {name} already exists. No action taken."
            else:
                ent = form.save()
                ent_pk = ent.pk

                col_pk = self.request.session.get("col_pk")
                log.info(f"col_pk from session is {col_pk}")
                imp_coll = Collection.objects.get(id=col_pk)
                ent.collection.add(imp_coll)
                save_to_created(self.request, ent)

                success = True
                res_msg = f"Created new {entity}-Object"

        else:
            success = False
            res_msg = f"{entity}-Object could not be created. Please check input."

        ent_pk = None
        if ent:
            ent_pk = ent.pk
        return JsonResponse(
                {
                    "call_function": call_function, "msg": res_msg, "form_name": form_name, "success": success,
                    "ent_type": entity, "created_pk": ent_pk
                })


class GenericItemCreateView(View):

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        model_name = kwargs.get("model_name")  # todo: __gpirgie__ make variable naming conform to the naming convention!

        module = sys.modules["apis_core.apis_vocabularies.models"]

        if get_subclass_dic(VocabsBaseClass, module).get(model_name):
            form = get_generic_vocabs_form(model_name)(self.request.POST)
        elif get_subclass_dic(AbstractRelationType, module).get(model_name):
            form = get_generic_relationtype_form(model_name)(self.request.POST)
        else:
            raise Http404

        form_name = model_name
        call_function = "CreateItem_response"

        if form.is_valid():
            name = self.request.POST["name"]
            success = True
         
            if not form.Meta.model.objects.filter(name=name).exists():
                ent = form.save()
                save_to_created(self.request, ent)
                res_msg = f"Created new {model_name}-Object"

            else:
                res_msg = f"{model_name}-Object already existed"

        else:
            success = False
            res_msg = f"{model_name}-Object could not be created. Please check input."

        return JsonResponse(
                {
                    "call_function": call_function, "msg": res_msg, "form_name": form_name, "success": success,
                    "ent_type": model_name
                })


class UpdatePageTokenView(View):
    template = "element_templates/page_token_form.html"
    log.info("called update Token")

    def post(self, *args, **kwargs):
        ds_pk = self.request.session.get("ds_pk")
        page_num = self.request.session.get("page_num")
        page_obj = DataSource.objects.get(id=ds_pk).get_page_object(page_num)
        page_obj.page_token = self.request.POST.get("page_token")
        page_obj.save()

        return JsonResponse({"success": True})


@login_required
def save_custom_ajax_form(request, entity_type, kind_form, SiteID,
                          ObjectID=False):
    # todo: __refactor__ __gpirgie__ I would only need project_pk and datapage_obj here.
    # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function if possible

    col_pk = request.session.get("col_pk")
    pagedata_pk = request.session.get("pagedata_pk")
    citation = request.session.get("citation")
    page_num = request.session.get("page_num")
    ds_pk = request.session.get("ds_pk")
    datasource = DataSource.objects.get(id=ds_pk)
    project_pk = request.session.get("project_pk")
    project = ImportProject.objects.get(pk=project_pk)

    if kind_form not in registered_forms.keys():
        raise Http404

    button_text = "create/modify"

    if not ObjectID:
        instance_id = ''
    else:
        instance_id = ObjectID
    entity_type_str = entity_type
    entity_type = AbstractEntity.get_entity_class_of_name(entity_type)
    log.info(f"entity type was {entity_type}, object_id = {ObjectID} = id of relation, kind_form {kind_form}")

    form_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)?(Highlighter)?Form', kind_form)
    form_dict = {
        'data': request.POST,
        'entity_type': entity_type,
        'request': request
    }

    test_form_relations = ContentType.objects.filter(
            model='{}{}'.format(form_match.group(1).lower(), form_match.group(2)).lower(),
            app_label='apis_relations')
    tab = re.match(r'(.*)Form', kind_form).group(1)
    call_function = 'EntityRelationForm_response'
    if test_form_relations.count() > 0:
        relation_form = test_form_relations[0].model_class()
        form_dict['relation_form'] = relation_form
        if form_match.group(3) == 'Highlighter':
            form_dict['highlighter'] = True
            tab = form_match.group(1) + form_match.group(2)
            call_function = 'HighlForm_response'
        form = CustomGenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[kind_form]
        form = form_class(**form_dict)

    if form.is_valid():
        site_instance = entity_type.objects.get(pk=SiteID)
        set_ann_proj = request.session.get('annotation_project', 1)
        entity_types_highlighter = request.session.get('entity_types_highlighter')
        users_show = request.session.get('users_show_highlighter', None)
        hl_text = None
        log.info(f"SiteID = {SiteID}, ObjectID {ObjectID}, site_instance {site_instance}, type: {type(site_instance)}")
        if ObjectID:
            rel_class = kind_form.rstrip("Form")
            log.info(f"KIND FORM is {kind_form}")
            if not kind_form == "PersonLabelForm":
                serialization_data = get_json_rel(rel_class=rel_class, rel_id=ObjectID)
            else:
                site_instance_serialization = get_json_entity(site_instance)

            instance = form.save(instance=ObjectID,
                                 site_instance=site_instance)

            if not instance.__class__.__name__ == "Label":
                save_to_edited(request, instance, project, serialization_data)
            else:
                save_to_edited(request, site_instance, project, site_instance_serialization)

        else:
            log.info(f"KIND FORM is {kind_form}")
            site_instance_serialization = get_json_entity(site_instance)
            instance = form.save(site_instance=site_instance)

            if not instance.__class__.__name__ == "Label":
                save_to_created(request, instance)
            else:
                save_to_edited(request, site_instance, project, site_instance_serialization)

        right_card = True
        if test_form_relations.count() > 0:
            table_html = form.get_html_table(entity_type_str, request, site_instance,
                                             form_match)
        if 'Highlighter' in tab or form_match.group(3) == 'Highlighter':
            hl_text = {
                'text': highlight_text(form.get_text_id(),
                                       users_show=users_show,
                                       set_ann_proj=set_ann_proj,
                                       types=entity_types_highlighter).strip(),
                'id': form.get_text_id()
            }
        if tab == 'PersonLabel':
            table_html = LabelTableEdit(
                    data=site_instance.label_set.all(),
                    prefix='PL-')
        elif tab == 'InstitutionLabel':
            table_html = LabelTableEdit(
                    data=site_instance.label_set.all(),
                    prefix='IL-')
        elif tab == 'PersonResolveUri':
            table_html = EntityUriTable(
                    Uri.objects.filter(entity=site_instance),
                    prefix='PURI-'
            )

        elif tab == 'AddRelationHighlighterPerson' or tab == 'PlaceHighlighter' or tab == 'PersonHighlighter' or tab \
                == 'SundayHighlighter':
            table_html = None
            right_card = False
            call_function = 'PAddRelation_response'
            instance = None
        if instance:
            instance2 = instance.get_web_object()
        else:
            instance2 = None
        if table_html:
            table_html2 = table_html.as_html(request)
        else:
            table_html2 = None

        col = Collection.objects.get(id=col_pk)
        pagedata = PageData.objects.get(id=pagedata_pk)

        def update_pagedata(instance, pagedata):
            inst = instance.related_institution
            func = instance.relation_type
            pagedata.institution = inst
            pagedata.function = func
            pagedata.save()

        page_token = datasource.get_page_token(page_num)
        log.info(f"page num was: {page_num}, page_token is {page_token}")

        log.info(f"instance name {instance}, {instance.__class__.__name__}")
        if not instance.__class__.__name__ == "Label":
            save_to_collection(instance, col)
            if request.POST.get("write citation"):
                save_citation(instance, citation, page_token)

        if kind_form == "PersonInstitutionForm":
            update_pagedata(instance, pagedata)

        data = {
            'test': True, 'tab': tab, 'call_function': call_function,
            'instance': instance2,
            'table_html': table_html2,
            'text': hl_text,
            'right_card': right_card
        }
    else:
        if 'Highlighter' in tab:
            call_function = 'HighlForm_response'

        data = {
            'test': False, 'call_function': call_function,
            'DivID': 'div_' + kind_form + instance_id,
            'form': render_to_string("element_templates/custom_ajax_form_generic.html", context={
                "entity_type": entity_type_str,
                "form": form, 'type1': kind_form, 'url2': 'save_ajax_' + kind_form,
                'button_text': button_text, 'ObjectID': ObjectID, 'SiteID': SiteID
            },
                                     request=request)
        }

    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def get_custom_ajax_form(request):
        # fixme: __maintainence__ __gpirgie__ Hook up with existing apis core function if possible

    '''Returns forms rendered in html'''
    FormName = request.POST.get('FormName')
    SiteID = request.POST.get('SiteID')
    log.info(f"SiteID-kwarg was {SiteID}, session ent_pk {request.session['ent_pk']}")
    ButtonText = request.POST.get('ButtonText')
    ObjectID = request.POST.get('ObjectID')
    entity_type_str = request.session.get('ent_type')
    pagedata_pk = request.session.get("pagedata_pk")

    form_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)(Highlighter)?Form', FormName)
    form_match2 = re.match(r'([A-Z][a-z]+)(Highlighter)?Form', FormName)
    if FormName and form_match:
        entity_type_v1 = ContentType.objects.filter(
                model='{}{}'.format(form_match.group(1).lower(), form_match.group(2)).lower(),
                app_label='apis_relations')
        entity_type_v2 = ContentType.objects.none()
    elif FormName and form_match2:
        entity_type_v2 = ContentType.objects.filter(
                model='{}'.format(
                        form_match.group(1).lower(),
                        app_label='apis_entities'))
        entity_type_v1 = ContentType.objects.none()
    else:
        entity_type_v1 = ContentType.objects.none()
        entity_type_v2 = ContentType.objects.none()
    if ObjectID == 'false' or ObjectID is None or ObjectID == 'None':
        ObjectID = False

        if FormName == "PersonInstitutionForm" and entity_type_str.lower() == "person":
            pd_obj = PageData.objects.get(id=pagedata_pk)
            pd_inst = pd_obj.institution
            pd_func = pd_obj.function
            form_dict = {'entity_type': entity_type_str, 'prefill_func': pd_func, 'prefill_inst': pd_inst}
        else:
            form_dict = {'entity_type': entity_type_str}
    elif entity_type_v1.count() > 0:
        d = entity_type_v1[0].model_class().objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}
    elif entity_type_v2.count() > 0:
        d = entity_type_v2[0].model_class().objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}
    else:
        if FormName not in registered_forms.keys():
            raise Http404
        d = registered_forms[FormName][0].objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}

    if entity_type_v1.count() > 0:
        form_dict['relation_form'] = '{}{}'.format(form_match.group(1), form_match.group(2))
        if form_match.group(3) == 'Highlighter':
            form_dict['highlighter'] = True
        form = CustomGenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[FormName]
        form = form_class(**form_dict)

    tab = FormName[:-4]

    data = {
        'tab': tab, 'form': render_to_string("element_templates/custom_ajax_form_generic.html", {
            "entity_type": entity_type_str,
            "form": form,
            'type1': FormName,
            'url2': 'save_ajax_' + FormName,
            'button_text': ButtonText,
            'ObjectID': ObjectID,
            'SiteID': SiteID,
        }, request)
    }

    return HttpResponse(json.dumps(data), content_type='application/json')


@method_decorator(login_required(), name="dispatch")
class CustomTableActionButtonView(View):

    def process_rel_date(self, rel, rel_class):
        # todo: __gpirgie__ viecpro_specific: consider saving "von" "bis" source attribute on update
        year = self.request.session.get("year")
        pk = self.kwargs.get("rel_pk")
        col_pk = self.request.session.get("col_pk")
        collection = Collection.objects.get(id=col_pk)

        citation = self.request.session.get("citation")
        page_num = self.request.session.get("page_num")

        project_pk = self.request.session.get("project_pk")
        project = ImportProject.objects.get(pk=project_pk)

        was_saved = True
        if year:
            year = int(year)
        # added custom test, for christian: add ab min. for schematismus 1811 and 1816
        if year in [1811, 1816]:
            year_written = f"ab min. {year}<{year}-06-30>"

        else:
            year_written = f"{year}<{year}-06-30>"
        #year_written = f"{year}<{year}-06-30>"
        serialization = get_json_rel(rel_id=rel.id,
                                     rel_class=rel_class.__name__)
        sd = rel.start_date
        ed = rel.end_date
        succ = False

        if sd and year < sd.year:
            rel.start_date_written = year_written

            msg = "updated start date"
            rel.save()
            rel = rel_class.objects.get(id=int(pk))

            assert rel.start_date.year == year
            succ = True

        elif (ed and ed.year < year) or (sd and sd.year < year and not ed):
            rel.end_date_written = year_written

            rel.save()
            msg = "updated end date"
            rel = rel_class.objects.get(id=int(pk))

            assert rel.end_date.year == year
            succ = True

        elif not (sd or ed):
            rel.end_date_written = year_written
            rel.start_date_written = year_written
            msg = "updated both dates"
            rel.save()
            rel = rel_class.objects.get(id=int(pk))

            assert rel.end_date.year == year == rel.start_date.year
            succ = True

        else:
            msg = "No action taken, dates didn't fit any given pattern."
            was_saved = False
            succ = True

        ds_pk = self.request.session.get("ds_pk")
        datasource = DataSource.objects.get(id=ds_pk)
        page_token = datasource.get_page_token(page_num)

        if was_saved:
            save_to_collection(rel, collection)
            save_citation(rel, citation, page_token)
            save_to_edited(self.request, rel, project, serialization)

        if not succ:
            msg = "An Error occured, relation left unchanged."
        return {"success": succ, "msg": msg}

    def get_table_html(self, ent_type, ent_inst, rel_class):
        entity_type = ent_type
        site_instance = ent_inst.pk
        table = get_generic_relations_table(relation_class=rel_class, entity_instance=ent_inst, detail=False)
        dic_a = {'related_' + entity_type.lower() + 'A': site_instance}
        dic_b = {'related_' + entity_type.lower() + 'B': site_instance}

        prefix = re.match(r'([A-Z][a-z])[^A-Z]*([A-Z][a-z])', rel_class.__name__)
        prefix = prefix.group(1) + prefix.group(2) + '-'
        form_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)', rel_class.__name__)

        if form_match.group(1) == form_match.group(2):
            dic_a = {'related_' + entity_type.lower() + 'A': site_instance}
            dic_b = {'related_' + entity_type.lower() + 'B': site_instance}
            objects = rel_class.objects.filter(
                    Q(**dic_a) | Q(**dic_b)
            )
        else:
            tab_query = {'related_' + entity_type.lower(): site_instance}
            objects = rel_class.objects.filter(**tab_query)

        table_instance = table(data=objects, prefix=prefix)
        table_html = table_instance.as_html(self.request)

        return table_html

    def post(self, *args, **kwargs):
        pk = self.kwargs.get("rel_pk")

        tab = self.request.POST.get("tab")
        rel_model_name = tab.replace("tab_", "")
        rel_class = AbstractRelation.get_relation_class_of_name(rel_model_name)
        rel = rel_class.objects.get(id=int(pk))
        ent_inst = rel.get_related_entity_instanceA()
        ent_type = ent_inst.__class__.__name__
        res_dic = self.process_rel_date(rel, rel_class)
        table_html = self.get_table_html(ent_type, ent_inst, rel_class)
        call_function = "TestFunction"  # todo: __gpirgie__ check if this is still used, otherwise remove it
        res_dic["call_function"] = call_function
        res_dic["tab"] = tab
        res_dic["table_html"] = table_html
        return JsonResponse(res_dic)
