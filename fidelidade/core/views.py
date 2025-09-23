from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Comercio, Promocao, Cliente, Pontuacao
from .forms import PromocaoForm, ComercioForm
import qr_code
from io import BytesIO
from django.core.files.base import ContentFile
import random
from django.utils import timezone

import qrcode


@login_required
def home(request):
    if request.user.tipo_usuario == 'comerciante':
        try:
            comercio = Comercio.objects.get(usuario=request.user)
            promocoes = Promocao.objects.filter(comercio=comercio)
            return render(request, 'core/comerciante_home.html', {
                'comercio': comercio,
                'promocoes': promocoes,
            })
        except Comercio.DoesNotExist:
            # Se for comerciante mas não tiver comércio cadastrado
            return redirect('editar_comercio')
    else:
        # Para clientes
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            pontuacoes = Pontuacao.objects.filter(cliente=cliente)
            return render(request, 'core/cliente_home.html', {
                'cliente': cliente,
                'pontuacoes': pontuacoes,
            })
        except Cliente.DoesNotExist:
            # Se não tiver perfil de cliente ainda, cria um
            cliente = Cliente.objects.create(usuario=request.user)
            return render(request, 'core/cliente_home.html', {
                'cliente': cliente,
                'pontuacoes': [],
            })

@login_required
def criar_promocao(request):
    if request.user.tipo_usuario != 'comerciante':
        return redirect('home')
    
    comercio = Comercio.objects.get(usuario=request.user)
    
    if request.method == 'POST':
        form = PromocaoForm(request.POST)
        if form.is_valid():
            promocao = form.save(commit=False)
            promocao.comercio = comercio
            promocao.save()  # Salva primeiro para ter um ID
            
            print(f"=== GERANDO QR CODE ===")
            print(f"Promoção ID: {promocao.id}")
            print(f"Promoção Nome: {promocao.nome}")
            
            # Gerar QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Dados únicos para o QR Code
            qr_data = f"promocao:{promocao.id}:{random.randint(1000, 9999)}"
            print(f"QR Data gerado: '{qr_data}'")
            
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Criar imagem do QR Code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvar a imagem no modelo
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            file_name = f'qr_{promocao.comercio.id}_{promocao.nome}.png'
            
            promocao.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
            promocao.save()
            
            print(f"QR Code salvo: {promocao.qr_code}")
            print("=== QR CODE GERADO COM SUCESSO ===")
            
            messages.success(request, 'Promoção criada com sucesso!')
            return redirect('home')
    else:
        form = PromocaoForm()
    
    return render(request, 'core/criar_promocao.html', {'form': form})

@login_required
def editar_promocao(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk, comercio__usuario=request.user)
    if request.method == 'POST':
        form = PromocaoForm(request.POST, instance=promocao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promoção atualizada com sucesso!')
            return redirect('detalhes_promocao', pk=promocao.id)
    else:
        form = PromocaoForm(instance=promocao)
    return render(request, 'core/editar_promocao.html', {'form': form, 'promocao': promocao})

@login_required
@require_POST  # Garante que só será acessada via POST
def excluir_promocao(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk, comercio__usuario=request.user)
    promocao.delete()
    messages.success(request, 'Promoção excluída com sucesso!')
    return redirect('home')



@login_required
def detalhes_promocao(request, pk):
    # Obtém a promoção ou retorna 404 se não existir
    promocao = get_object_or_404(Promocao, pk=pk, comercio__usuario=request.user)
    
    # Obtém todas as pontuações relacionadas a esta promoção
    pontuacoes = Pontuacao.objects.filter(promocao=promocao)
    
    return render(request, 'core/detalhes_promocao.html', {
        'promocao': promocao,
        'pontuacoes': pontuacoes
    })

import logging
logger = logging.getLogger(__name__)

@login_required
def ler_qr_code(request):
    if request.user.tipo_usuario != 'cliente':
        return JsonResponse({'success': False, 'error': 'Apenas clientes podem ler QR Codes'})
    
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '').strip()
        
        print(f"=== NOVA LEITURA ===")
        print(f"Usuário: {request.user.username}")
        print(f"QR Code: {qr_data}")
        
        try:
            # Verificar formato básico
            if not qr_data or 'promocao:' not in qr_data:
                return JsonResponse({'success': False, 'error': 'QR Code inválido ou vazio'})
            
            parts = qr_data.split(':')
            if len(parts) < 2:
                return JsonResponse({'success': False, 'error': 'Formato de QR Code inválido'})
            
            promocao_id = parts[1].strip()
            if not promocao_id.isdigit():
                return JsonResponse({'success': False, 'error': 'ID da promoção inválido'})
            
            # Buscar promoção
            promocao = Promocao.objects.get(id=int(promocao_id), ativa=True)
            cliente = Cliente.objects.get(usuario=request.user)
            
            # Verificar datas
            hoje = timezone.now().date()
            if promocao.data_inicio > hoje:
                return JsonResponse({'success': False, 'error': f'Promoção inicia em {promocao.data_inicio}'})
            
            if promocao.data_fim < hoje:
                return JsonResponse({'success': False, 'error': f'Promoção expirou em {promocao.data_fim}'})
            
            # Verificar se já existe pontuação
            pontuacao, created = Pontuacao.objects.get_or_create(
                cliente=cliente,
                promocao=promocao,
                defaults={'pontos': 1}
            )
            
            pontos_adicionados = 0
            
            if not created:
                if pontuacao.resgatado:
                    return JsonResponse({'success': False, 'error': 'Prêmio já resgatado para esta promoção'})
                
                if pontuacao.pontos < promocao.pontos_necessarios:
                    pontuacao.pontos += 1
                    pontuacao.save()
                    pontos_adicionados = 1
                else:
                    return JsonResponse({'success': False, 'error': 'Pontuação máxima já atingida'})
            else:
                pontos_adicionados = 1
            
            print(f"Pontos adicionados: {pontos_adicionados}")
            print(f"Total: {pontuacao.pontos}/{promocao.pontos_necessarios}")
            
            return JsonResponse({
                'success': True,
                'promocao_nome': promocao.nome,
                'pontos': pontuacao.pontos,
                'necessarios': promocao.pontos_necessarios,
                'premio': promocao.premio,
                'comercio': promocao.comercio.nome_fantasia,
                'pontos_adicionados': pontos_adicionados,
                'message': f'✅ {pontos_adicionados} ponto(s) adicionado(s) com sucesso!'
            })
            
        except Promocao.DoesNotExist:
            print("ERRO: Promoção não encontrada")
            return JsonResponse({'success': False, 'error': 'Promoção não encontrada ou inativa'})
        except Cliente.DoesNotExist:
            print("ERRO: Cliente não encontrado")
            return JsonResponse({'success': False, 'error': 'Perfil de cliente não encontrado'})
        except Exception as e:
            print(f"ERRO: {e}")
            return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})
    
    return render(request, 'core/ler_qr_code.html')

@login_required
def resgatar_premio(request, pontuacao_id):
    if request.user.tipo_usuario != 'cliente':
        return redirect('home')
    
    pontuacao = get_object_or_404(Pontuacao, id=pontuacao_id, cliente__usuario=request.user)
    
    if pontuacao.pontos >= pontuacao.promocao.pontos_necessarios and not pontuacao.resgatado:
        pontuacao.resgatado = True
        pontuacao.save()
        messages.success(request, f'Prêmio "{pontuacao.promocao.premio}" resgatado com sucesso!')
    else:
        messages.error(request, 'Não foi possível resgatar este prêmio.')
    
    return redirect('home')

@login_required
def editar_comercio(request):
    if request.user.tipo_usuario != 'comerciante':
        return redirect('home')
    
    comercio = Comercio.objects.get(usuario=request.user)
    
    if request.method == 'POST':
        form = ComercioForm(request.POST, instance=comercio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informações atualizadas com sucesso!')
            return redirect('home')
    else:
        form = ComercioForm(instance=comercio)
    
    return render(request, 'core/editar_comercio.html', {'form': form})