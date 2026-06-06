from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views.outras_entradas import OutraEntradaViewSet
from .views.import_outras_entradas import OutraEntradaImportView

router = SimpleRouter()
router.register(r"", OutraEntradaViewSet, basename="outra-entrada")

urlpatterns = [
    path("import/", OutraEntradaImportView.as_view(), name="outras-entradas-import-bulk"),
    path("", include(router.urls)),
]
