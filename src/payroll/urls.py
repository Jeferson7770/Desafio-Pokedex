from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.prolabore import ProLaboreViewSet

router = DefaultRouter()
router.register(r'', ProLaboreViewSet, basename='pro-labore')

urlpatterns = [
    path('', include(router.urls)),
]