from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('cliente', 'Cliente'),
        ('comerciante', 'Comerciante'),
    ]
    
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True, unique=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    email_confirmado = models.BooleanField(default=False)
    
    name = models.CharField(max_length=180, blank=True, verbose_name='Nome Completo')
    
    
    def __str__(self):
        return self.username
    
    def clean(self):
        super().clean()
        if self.tipo_usuario == 'cliente' and not self.cpf:
            raise ValidationError(_('Clientes devem ter CPF cadastrado.'))
        if self.tipo_usuario == 'comerciante' and not self.cnpj:
            raise ValidationError(_('Comerciantes devem ter CNPJ cadastrado.'))
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'