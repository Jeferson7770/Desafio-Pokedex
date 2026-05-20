from django.urls import path

from ..users.views.laywer import LawyerProfileViewSet
from .views.register import RegisterView
from .views.login import LoginView
from .views.logout import LogoutView
from .views.reset_password import RequestPasswordResetView, ConfirmPasswordResetView

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
    
    path('password-reset/', RequestPasswordResetView.as_view()),
    path('password-reset-confirm/', ConfirmPasswordResetView.as_view()),
]