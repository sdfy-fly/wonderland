from django.contrib import admin
from .models import Account


@admin.register(Account)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'firstName', 'lastName', 'email', 'password')
    search_fields = ('id', 'firstName')
    list_editable = ('firstName', 'lastName', 'email', 'password')
