from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("src.users.urls")),
    path("api/firms/", include("src.firms.urls")),
    path("api/expenses/", include("src.expenses.urls")),
    path("api/relatorios/", include("src.relatorios.urls")),
    path("api/dinheiro/", include("src.dinheiro.urls")),
    path("api/motor/", include("src.motor.urls")),
    path("api/prolabore/", include("src.prolabore.urls")),
    path("api/suggestions/", include("src.suggestions.urls")),
    path("api/honorarios/", include("src.honorarios.urls")),
    path("api/cases/", include("src.cases.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
