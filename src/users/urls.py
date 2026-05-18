from django.urls import path

from fincecore.src.users.views.logout import LogoutView

from ..users.views.laywer import LawyerProfileView
from .views.register import (
    RegisterView,
)

from .views.login import (
    LoginView
)

from .views.reset_password import (
    RequestPasswordResetView,
    ConfirmPasswordResetView
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('laywer-profile/', LawyerProfileView.as_view()),
    path('password-reset/', RequestPasswordResetView.as_view()),
    path('password-reset-confirm/', ConfirmPasswordResetView.as_view()),
]