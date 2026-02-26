from django.db import models
from accounts.models import CustomUser
from django.core.validators import MinValueValidator

class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.nome} - {self.estado}"

    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        unique_together = ('nome', 'estado')

class Comercio(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='comercio')
    nome_fantasia = models.CharField(max_length=100)
    razao_social = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    cidade = models.ForeignKey(Cidade, on_delete=models.PROTECT, related_name='comercios')
    telefone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
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
    data_fim = models.DateField(null=True, blank=True)
    sem_prazo = models.BooleanField(default=False, verbose_name="Sem data de validade")
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
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    promocao = models.ForeignKey(Promocao, on_delete=models.CASCADE)
    pontos = models.IntegerField(default=0)
    resgatado = models.BooleanField(default=False)
    data_resgate = models.DateTimeField(null=True, blank=True)
    codigo_resgate = models.CharField(max_length=5, blank=True, null=True, unique=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def gerar_codigo_resgate(self):
        import random
        import string
        
        # Gerar código único de 5 dígitos alfanumérico
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            if not Pontuacao.objects.filter(codigo_resgate=codigo).exists():
                self.codigo_resgate = codigo
                break
        return codigo

    def __str__(self):
        return f"{self.cliente.usuario.username} - {self.promocao.nome} ({self.pontos} pts)"