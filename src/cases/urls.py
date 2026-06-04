from django.urls import path
from rest_framework.routers import DefaultRouter
from ..cases.views.import_clients import ClientImportView
from ..cases.views.case import CaseViewSet, ClientViewSet, ProcessViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="clients")
router.register("processes", ProcessViewSet, basename="processes")
router.register("", CaseViewSet, basename="cases")

urlpatterns = [
	path("clients/import/", ClientImportView.as_view(), name="clients-import"),
	*router.urls,
]