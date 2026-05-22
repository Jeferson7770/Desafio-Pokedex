from django.contrib import admin

from .models.expenses import Expense

admin.site.register(Expense)