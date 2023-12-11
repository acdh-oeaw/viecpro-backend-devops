import os
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView


from apis_core.apis_entities.api_views import GetEntityGeneric



urlpatterns = [
    url(r"^apis/", include("apis_core.urls", namespace="apis")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        r"entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
    ),
    url(r"^admin/", admin.site.urls),
    url(r"^info/", include("infos.urls", namespace="info")),
    url(r"^", include("webpage.urls", namespace="webpage")),
]


if 'viecpro_hierarchy' in settings.INSTALLED_APPS:
    urlpatterns.insert(0, url(r'^visualisations/', include("viecpro_hierarchy.urls", namespace="viecpro_hierarchy"))
    )

if 'viecpro_import' in settings.INSTALLED_APPS:
    urlpatterns = urlpatterns + [
         url(r'^viecpro_import/', include("viecpro_import.urls", namespace="viecpro_import"))]

if 'viecpro_deduplication' in settings.INSTALLED_APPS:
    urlpatterns = urlpatterns + [
        url(r'^dubletten/', include("viecpro_deduplication.urls", namespace="viecpro_deduplication")),
        ]

if "apis_bibsonomy" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(r"^bibsonomy/", include("apis_bibsonomy.urls", namespace="bibsonomy"))
    )

if "apis_ampel" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(
            r"^apis_ampel/",
            include("apis_ampel.urls", namespace="apis_ampel"),
        )
    )

if "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(r"^__debug__/", include('debug_toolbar.urls'))
    ) 

# robots.txt route
# handling of robots.txt files on instance-basis can be configured in settings
if os.path.exists(os.path.join(settings.ROBOTS_TXT_FOLDER,  "robots.txt")):
        urlpatterns.append(
    path("robots.txt", TemplateView.as_view(
    template_name="robots.txt", content_type="text/plain")),
    )

handler404 = "webpage.views.handler404"
