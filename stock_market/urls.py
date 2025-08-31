from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Stock Market API",
        default_version='v1',
        description="API для симуляции биржевой торговли",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url="https://pseudo-stock.org",
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('market.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
