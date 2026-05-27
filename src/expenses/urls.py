from django.urls import path, include
from rest_framework.routers import DefaultRouter
from src.expenses.views.expenses import ExpenseViewSet
from src.expenses.views.import_expenses import ExpenseImportView

router = DefaultRouter()
router.register("", ExpenseViewSet, basename="expenses")

urlpatterns = [
    path("import/", ExpenseImportView.as_view(), name="expense-import"),
    path("", include(router.urls)),
]