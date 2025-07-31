from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.core.exceptions import ValidationError
import re

class ClienteRegistrationForm(UserCreationForm):
    cpf = forms.CharField(max_length=14, required=True, help_text='Formato: 000.000.000-00')
    email = forms.EmailField(required=True)
    name = forms.CharField(required=True, label='Nome Completo', max_length=180)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'name', 'cpf', 'password1', 'password2']
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            raise ValidationError('CPF deve estar no formato 000.000.000-00')
        return cpf
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo_usuario = 'cliente'
        user.cpf = self.cleaned_data['cpf']
        if commit:
            user.save()
        return user

class ComercianteRegistrationForm(UserCreationForm):
    cnpj = forms.CharField(max_length=18, required=True, help_text='Formato: 00.000.000/0000-00')
    email = forms.EmailField(required=True)
    name = forms.CharField(required=True, label='Nome Completo', max_length=180)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'name', 'cnpj', 'password1', 'password2']
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if not re.match(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', cnpj):
            raise ValidationError('CNPJ deve estar no formato 00.000.000/0000-00')
        return cnpj
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo_usuario = 'comerciante'
        user.cnpj = self.cleaned_data['cnpj']
        if commit:
            user.save()
        return user