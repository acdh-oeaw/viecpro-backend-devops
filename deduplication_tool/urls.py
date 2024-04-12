from django.urls import path, include
from django.views.generic import TemplateView
from deduplication_tool.api.urls import urlpatterns as api_urls
from deduplication_tool.views import ActionHandler
from .views import EditorView
app_name = "deduplication_tool"
urlpatterns = [
    path("/test", EditorView.as_view(), name="deduplication-test"),
    path("/actions/<str:action>/", ActionHandler.as_view()),
    path("/api", include(api_urls)),
]