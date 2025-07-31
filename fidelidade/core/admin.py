from django.contrib import admin
from .models import Comercio, Promocao, Cliente, Pontuacao

@admin.register(Comercio)
class ComercioAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'razao_social', 'cidade', 'estado')
    search_fields = ('nome_fantasia', 'razao_social', 'cnpj')

@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'comercio', 'premio', 'pontos_necessarios', 'ativa')
    list_filter = ('ativa', 'comercio')
    search_fields = ('nome', 'premio')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'data_nascimento', 'data_cadastro')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__cpf')

@admin.register(Pontuacao)
class PontuacaoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'promocao', 'pontos', 'resgatado')
    list_filter = ('resgatado', 'promocao__comercio')
    search_fields = ('cliente__usuario__first_name', 'promocao__nome')