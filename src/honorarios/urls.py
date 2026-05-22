from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views.honorarios import HonorarioViewSet

router = SimpleRouter()
router.register(r"", HonorarioViewSet, basename="honorario")

urlpatterns = [
    path("", include(router.urls)),
]