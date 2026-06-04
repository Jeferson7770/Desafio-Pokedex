from django.urls import path

from ..users.views.notifications import NotificationSettingViewSet

from .views.billing import SubscriptionViewSet
from .views.subscription import CriarAssinaturaView
from ..users.views.laywer import LawyerProfileViewSet
from .views.register import RegisterView
from .views.login import LoginView
from .views.logout import LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('laywer-profile/', LawyerProfileViewSet.as_view({
        'get': 'list',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('laywer-profile/change-password/', LawyerProfileViewSet.as_view({
        'post': 'change_password'
    })),
    path('billing/subscription/', SubscriptionViewSet.as_view({
        'get': 'list'
    })),
    path('billing/subscription/upgrade/', SubscriptionViewSet.as_view({
        'post': 'prepare_upgrade'
    })),
    path('billing/subscription/cancel/', SubscriptionViewSet.as_view({
        'post': 'prepare_cancel'
    })),
    path('subscription/checkout/', CriarAssinaturaView.as_view()),
    path('billing/subscription/checkout/', CriarAssinaturaView.as_view()),
    path('notifications/settings/', NotificationSettingViewSet.as_view({
        'get': 'list',
        'put': 'update',
        'patch': 'partial_update'
    })),
    path('laywer-profile/disconnect-device/<int:device_pk>/', LawyerProfileViewSet.as_view({
        'post': 'disconnect_device'
    })),
    path('laywer-profile/disconnect-all-devices/', LawyerProfileViewSet.as_view({
        'post': 'disconnect_all_devices'
    })),
    path('laywer-profile/delete-account/', LawyerProfileViewSet.as_view({
        'post': 'delete_account'
    })),
]