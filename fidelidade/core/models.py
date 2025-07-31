from django.db import models
from accounts.models import CustomUser
from django.core.validators import MinValueValidator

class Comercio(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='comercio')
    nome_fantasia = models.CharField(max_length=100)
    razao_social = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome_fantasia
    
    class Meta:
        verbose_name = 'Comércio'
        verbose_name_plural = 'Comércios'

class Promocao(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE, related_name='promocoes')
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    pontos_necessarios = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    premio = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativa = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.nome} - {self.comercio.nome_fantasia}"
    
    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'

class Cliente(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cliente')
    data_nascimento = models.DateField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

class Pontuacao(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pontuacoes')
    promocao = models.ForeignKey(Promocao, on_delete=models.CASCADE, related_name='pontuacoes')
    pontos = models.PositiveIntegerField(default=0)
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    resgatado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.cliente} - {self.promocao}: {self.pontos}/{self.promocao.pontos_necessarios}"
    
    class Meta:
        verbose_name = 'Pontuação'
        verbose_name_plural = 'Pontuações'
        unique_together = ('cliente', 'promocao')