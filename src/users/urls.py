from django.urls import path

from fincecore.src.expenses.models.expenses import Expense

from ..users.views.laywer import LawyerProfileView
from .views.register import (
    RegisterView,
)

from .views.login import (
    LoginView
)

from .views.logout import (
    LogoutView
)

from .views.reset_password import (
    RequestPasswordResetView,
    ConfirmPasswordResetView
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('expenses/', Expense.as_view()),
    path('laywer-profile/', LawyerProfileView.as_view()),
    path('password-reset/', RequestPasswordResetView.as_view()),
    path('password-reset-confirm/', ConfirmPasswordResetView.as_view()),
]