from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from accounts.views import (
    register_cliente,
    register_comerciante,
    confirm_email,
    custom_logout
)
from core import views as core_views

from django.conf import settings
from django.conf.urls.static import static
from core.views import excluir_promocao

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    
    # Cadastro
    path('registrar/cliente/', register_cliente, name='register_cliente'),
    path('registrar/comerciante/', register_comerciante, name='register_comerciante'),
    path('confirmar-email/<uidb64>/<token>/', confirm_email, name='confirm_email'),
    
    # Core
    path('', core_views.home, name='home'),
    path('selecionar-cidade/', core_views.selecionar_cidade, name='selecionar_cidade'),
    path('criar-promocao/', core_views.criar_promocao, name='criar_promocao'),
    path('ler-qr-code/', core_views.ler_qr_code, name='ler_qr_code'),
    path('resgatar-premio/<int:pontuacao_id>/', core_views.resgatar_premio, name='resgatar_premio'),
    path('editar-comercio/', core_views.editar_comercio, name='editar_comercio'),
    
    path('promocao/<int:pk>/', core_views.detalhes_promocao, name='detalhes_promocao'),
    path('promocao/editar/<int:pk>/', core_views.editar_promocao, name='editar_promocao'),
    path('promocao/excluir/<int:pk>/', excluir_promocao, name='excluir_promocao'),
    
    # Resgate
    path('painel-resgate/', core_views.painel_resgate_comerciante, name='painel_resgate'),
    path('resgatar-premio-comerciante/', core_views.resgatar_premio_comerciante, name='resgatar_premio_comerciante'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)