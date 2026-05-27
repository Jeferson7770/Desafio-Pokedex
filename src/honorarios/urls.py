from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views.honorarios import HonorarioViewSet
from .views.import_honorarios import HonorarioImportView

router = SimpleRouter()
router.register(r"", HonorarioViewSet, basename="honorario")

urlpatterns = [
    path("import/", HonorarioImportView.as_view(), name="honorarios-import-bulk"),
    path("", include(router.urls)),
]