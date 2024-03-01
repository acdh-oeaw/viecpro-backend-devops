from django.urls import include, path

from .views import EditorAllSectionsView, \
    GenericEntitiesCreateView, GenericEntitiesUpdateView, GenericItemCreateView, get_custom_ajax_form, \
    save_custom_ajax_form, CustomTableActionButtonView, ds_select_post, set_start_page, update_browser, \
    editor_session_update, \
    UpdatePageTokenView, editor_update_section, EditorPageView, editor_autocomplete, ProjectPageView, \
    update_datasource, upload_pdf, create_import_project, edit_import_project, update_datasource_select_ajax

from django.conf.urls import url

app_name = 'apis_import_project'

editor_patterns = [
    url(r'^(?P<project_pk>[0-9]+)/$', EditorPageView.as_view(), name='editor_main'),
    url(r'^session/update$', editor_session_update, name='editor_session_update'),
    url(r'^section/all/$',
        EditorAllSectionsView.as_view(),
        name='get_sections', ),
    url(r'^section/update/(?P<section>[A-Za-z]+)/$', editor_update_section, name='editor_section_update'),
    url(r'^autocomplete/(?P<entity>[a-zA-Z]+)/$', editor_autocomplete, name='editor_autocomplete'),

    url(r'^entity/create/(?P<entity>[a-zA-Z]+)/$',
        GenericEntitiesCreateView.as_view(),
        name='entity_create', ),
    url(r'^entity/update/(?P<entity>[a-zA-Z]+)/(?P<pk>[0-9]+)/$',
        GenericEntitiesUpdateView.as_view(),
        name='entity_update', ),
    url(r'^item/create/(?P<model_name>[A-Za-z]+)$',
        GenericItemCreateView.as_view(),
        name='item_create', ),

    url(r'^relation/getform/$', get_custom_ajax_form, name='relation_get_form'),
    url(r'^relation/autodate/(?P<rel_pk>[0-9]+)/(?P<tab>[a-zA-Z_]+)/$', CustomTableActionButtonView.as_view(),
        name='relation_autodate'),
    url(
            r'^relation/update/(?P<col_pk>[0-9]+)/(?P<pagedata_pk>[0-9]+)/(?P<entity_type>[a-zA-z]+)/(?P<kind_form>['
            r'a-zA-z]+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>[0-9]*))?/$',
            save_custom_ajax_form, name='relation_update_or_create'
    ),
    url(
            r'^relation/create/(?P<entity_type>[a-zA-z]+)/(?P<kind_form>[a-zA-z]+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>['
            r'0-9]*))?/$',
            save_custom_ajax_form, name='relation_update_or_create'
    ),

]

datasource_patterns = [
    url(r'^select/$', ds_select_post, name='ds_select'),
    url(r'^upload/$', upload_pdf, name='ds_upload'),
    url(r'^page/update/$', UpdatePageTokenView.as_view(), name='page_set_token'),
    url(r'^update/$', update_datasource, name='ds_update'),
    url(r'^update_select/$', update_datasource_select_ajax, name='ds_list_refresh'),
    url(r'^page/update/start$', set_start_page, name='page_set_start'),

]

browser_patterns = [
    url(r'^refresh/$', update_browser,
        name='browser_refresh'),
    url(r'^refresh/(?P<project_pk>[0-9]+)/(?P<data_source_pk>[0-9]+)/(?P<page_num>[0-9]+)/(?P<direction>[a-z]+)/$',
        update_browser,
        name='browser_refresh'),
]

project_patterns = [
    path('', ProjectPageView.as_view(), name='project_main'),
    url(r'^create/$', create_import_project, name='project_create'),
    url(r'^update/(?P<project_pk>[0-9]+)/$', edit_import_project, name='project_update'),
]

urlpatterns = [
    path('editor/', include(editor_patterns)),
    path('datasource/', include(datasource_patterns)),
    path('project/', include(project_patterns)),
    path('browser/', include(browser_patterns)),
]
