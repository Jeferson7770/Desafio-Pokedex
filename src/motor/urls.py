from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.motor import MotorPrioridadeViewSet

router = DefaultRouter()
router.register("", MotorPrioridadeViewSet, basename="motor-prioridade")

urlpatterns = [
    path("", include(router.urls)),
]