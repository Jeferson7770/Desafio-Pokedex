from rest_framework.routers import DefaultRouter
from src.expenses.views.expenses import ExpenseViewSet
from src.expenses.views.import_expenses import ExpenseImportView

router = DefaultRouter()
router.register("", ExpenseViewSet, basename="expenses")
router.register("import/", ExpenseImportView, basename="expense-import")


urlpatterns = router.urls