from rest_framework.routers import DefaultRouter
from ..cases.views.case import CaseViewSet, ClientViewSet, ProcessViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="clients")
router.register("processes", ProcessViewSet, basename="processes")
router.register("", CaseViewSet, basename="cases")

urlpatterns = router.urls