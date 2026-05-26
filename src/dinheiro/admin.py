from django.contrib import admin
from .models.dinheiro import BankAccount, Transaction

admin.site.register(BankAccount)
admin.site.register(Transaction)