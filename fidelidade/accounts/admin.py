from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'tipo_usuario')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('name', 'email')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Outros', {'fields': ('tipo_usuario', 'cpf', 'cnpj', 'telefone', 'email_confirmado')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)