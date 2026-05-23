from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.relatorios import FinancialReportViewSet

router = DefaultRouter()
router.register(r'', FinancialReportViewSet, basename='financial-report')

urlpatterns = [
    path('', include(router.urls)),
]