from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.dinheiro import BankAccountViewSet, TransactionViewSet, FinanceDashboardSummaryView

router = DefaultRouter()
router.register(r'accounts', BankAccountViewSet, basename='bank-account')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-summary/', FinanceDashboardSummaryView.as_view(), name='finance-dashboard-summary'),
]