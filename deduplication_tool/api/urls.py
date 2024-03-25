from django.urls import path, include
from . routers import router 
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView

urlpatterns = [
    path('', include(router.urls)), # type: ignore
    path('/api-auth/', include("rest_framework.urls")),
    path('/schema', SpectacularAPIView.as_view(), name='deduplication_api_schema'),
    path('/schema/swagger-ui', SpectacularSwaggerView.as_view(url_name="deduplication_tool:deduplication_api_schema"), name="deduplication-swagger-ui"),

]