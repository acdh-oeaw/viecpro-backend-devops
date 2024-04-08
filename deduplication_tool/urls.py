from django.urls import path, include
from django.views.generic import TemplateView
from deduplication_tool.api.urls import urlpatterns as api_urls
from deduplication_tool.views import ActionHandler

app_name = "deduplication_tool"
urlpatterns = [
    path("/test", TemplateView.as_view(template_name="deduplication_tool/tool_page.html"), name="deduplication-test"),
    path("/actions/<str:action>/", ActionHandler.as_view()),
    path("/api", include(api_urls)),
]