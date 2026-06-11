from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from src.firms.views.webhook import AbacatePayWebhookView

urlpatterns = [
    path("fince-admin/", admin.site.urls),
    path("api/auth/", include("src.users.urls")),
    path("api/firms/", include("src.firms.urls")),
    path("api/expenses/", include("src.expenses.urls")),
    path("api/reports/", include("src.reports.urls")),
    path("api/relatorios/", include("src.reports.urls")),
    path("api/finance/", include("src.finance.urls")),
    path("api/motor/", include("src.motor.urls")),
    path("api/payroll/", include("src.payroll.urls")),
    path("api/prolabore/", include("src.payroll.urls")),
    path("api/suggestions/", include("src.suggestions.urls")),
    path("api/fees/", include("src.fees.urls")),
    path("api/honorarios/", include("src.fees.urls")),
    path("api/other-income/", include("src.other_income.urls")),
    path("api/outras-entradas/", include("src.other_income.urls")),
    path("api/cases/", include("src.cases.urls")),
    path("api/webhooks/abacatepay/", AbacatePayWebhookView.as_view()),
]

if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
        SpectacularRedocView,
    )
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
