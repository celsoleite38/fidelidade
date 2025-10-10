from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

#from fidelidade.accounts import models
from .models import Comercio, Promocao, Cliente, Pontuacao
from .forms import PromocaoForm, ComercioForm
import qr_code
from io import BytesIO
from django.core.files.base import ContentFile
import random
from django.utils import timezone

import qrcode

from django.db.models import F, Count, Q

@login_required

def home(request):
    if request.user.tipo_usuario == 'comerciante':
        try:
            comercio = Comercio.objects.get(usuario=request.user)
            promocoes = Promocao.objects.filter(comercio=comercio)
            
            total_pontuacoes = Pontuacao.objects.filter(
                promocao__comercio=comercio
            ).count()
            # === NOVAS ESTATÍSTICAS ADICIONADAS AQUI ===
            # Total de pontuações registradas
            total_pontuacoes = Pontuacao.objects.filter(
                promocao__comercio=comercio
            ).count()
            
            # Resgates pendentes (atingiram a meta mas não resgataram)
            resgates_pendentes = Pontuacao.objects.filter(
                promocao__comercio=comercio,
                pontos__gte=F('promocao__pontos_necessarios'),
                resgatado=False
            ).count()
            # === FIM DAS NOVAS ESTATÍSTICAS ===
            
            return render(request, 'core/comerciante_home.html', {
                'comercio': comercio,
                'promocoes': promocoes,
                # === NOVOS CONTEXTOS ADICIONADOS ===
                'total_pontuacoes': total_pontuacoes,
                'resgates_pendentes': resgates_pendentes,
                # === FIM DOS NOVOS CONTEXTOS ===
            })
        except Comercio.DoesNotExist:
            # Se for comerciante mas não tiver comércio cadastrado
            return redirect('editar_comercio')
    else:
        # Para clientes (mantido igual)
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
            qr_data = f"promocao:{promocao.id}"
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
    pontuacoes = Pontuacao.objects.filter(promocao=promocao)
    for pontuacao in pontuacoes:
        pontuacao.pontos_faltantes = pontuacao.promocao.pontos_necessarios - pontuacao.pontos
        
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
        # Verificar se é upload de imagem ou dados diretos
        if 'qr_image' in request.FILES:
            # Processar upload de imagem
            return processar_imagem_qr_code(request)
        else:
            # Processar dados diretos do scanner (código atual)
            return processar_dados_qr_code(request)
    
    return render(request, 'core/ler_qr_code.html')

def processar_dados_qr_code(request):
    """Processa dados de QR code do scanner JavaScript"""
    qr_data = request.POST.get('qr_data', '').strip()
    
    print(f"=== NOVA LEITURA ===")
    print(f"Usuário: {request.user.username}")
    print(f"QR Code: {qr_data}")
    
    try:
        # Verificar formato básico
        if not qr_data or not qr_data.startswith('promocao:'):
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
        
        # === NOVO CÓDIGO AQUI ===
        # Verificar se atingiu a pontuação necessária para gerar código de resgate
        premio_disponivel = False
        codigo_resgate = None
        
        if pontuacao.pontos >= promocao.pontos_necessarios and not pontuacao.resgatado:
            premio_disponivel = True
            # Gerar código de resgate se ainda não tiver
            if not pontuacao.codigo_resgate:
                codigo_resgate = gerar_codigo_resgate(pontuacao)
                pontuacao.save()
                print(f"Código de resgate gerado: {codigo_resgate}")
            else:
                codigo_resgate = pontuacao.codigo_resgate
                print(f"Código de resgate existente: {codigo_resgate}")
        # === FIM DO NOVO CÓDIGO ===
        
        response = {
            'success': True,
            'promocao_nome': promocao.nome,
            'pontos': pontuacao.pontos,
            'necessarios': promocao.pontos_necessarios,
            'premio': promocao.premio,
            'comercio': promocao.comercio.nome_fantasia,
            'pontos_adicionados': pontos_adicionados,
            # === NOVOS CAMPOS ADICIONADOS ===
            'premio_disponivel': premio_disponivel,
            'codigo_resgate': codigo_resgate,
            # === FIM DOS NOVOS CAMPOS ===
            'message': f'✅ {pontos_adicionados} ponto(s) adicionado(s) com sucesso!'
        }
        
        return JsonResponse(response)
        
    except Promocao.DoesNotExist:
        print("ERRO: Promoção não encontrada")
        return JsonResponse({'success': False, 'error': 'Promoção não encontrada ou inativa'})
    except Cliente.DoesNotExist:
        print("ERRO: Cliente não encontrado")
        return JsonResponse({'success': False, 'error': 'Perfil de cliente não encontrado'})
    except Exception as e:
        print(f"ERRO: {e}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})

# === ADICIONE ESTA FUNÇÃO NOVA ===
def gerar_codigo_resgate(pontuacao):
    """Gera um código de resgate único de 5 dígitos"""
    import random
    import string
    
    # Gerar código único de 5 dígitos alfanumérico
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not Pontuacao.objects.filter(codigo_resgate=codigo).exists():
            pontuacao.codigo_resgate = codigo
            break
    return codigo

# views.py - adicione estas views
@login_required
def painel_resgate_comerciante(request):
    """Painel onde o comerciante pode resgatar prêmios"""
    if request.user.tipo_usuario != 'comerciante':
        return redirect('home')
    
    comercio = Comercio.objects.get(usuario=request.user)
    promocoes = Promocao.objects.filter(comercio=comercio)
    
    # Pontuações prontas para resgate das promoções do comerciante
    pontuacoes_resgate = Pontuacao.objects.filter(
        promocao__comercio=comercio,
        pontos__gte=F('promocao__pontos_necessarios'),
        resgatado=False
    ).select_related('cliente', 'promocao')
    
    return render(request, 'core/painel_resgate.html', {
        'comercio': comercio,
        'pontuacoes_resgate': pontuacoes_resgate,
        'promocoes': promocoes,
    })

@login_required
@require_POST
def resgatar_premio_comerciante(request):
    """View para o comerciante confirmar o resgate usando o código"""
    if request.user.tipo_usuario != 'comerciante':
        return JsonResponse({'success': False, 'error': 'Apenas comerciantes podem resgatar prêmios'})
    
    codigo = request.POST.get('codigo', '').strip().upper()
    
    if not codigo:
        return JsonResponse({'success': False, 'error': 'Código de resgate é obrigatório'})
    
    try:
        pontuacao = Pontuacao.objects.get(
            codigo_resgate=codigo,
            resgatado=False
        )
        
        # Verificar se a promoção pertence ao comerciante
        if pontuacao.promocao.comercio.usuario != request.user:
            return JsonResponse({'success': False, 'error': 'Este código não pertence ao seu estabelecimento'})
        
        # Verificar se atingiu a pontuação necessária
        if pontuacao.pontos < pontuacao.promocao.pontos_necessarios:
            return JsonResponse({'success': False, 'error': 'Pontuação insuficiente para resgate'})
        
        # Realizar o resgate
        pontuacao.resgatado = True
        pontuacao.data_resgate = timezone.now()
        pontuacao.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Prêmio resgatado com sucesso!',
            'cliente': pontuacao.cliente.usuario.get_full_name() or pontuacao.cliente.usuario.username,
            'promocao': pontuacao.promocao.nome,
            'premio': pontuacao.promocao.premio
        })
        
    except Pontuacao.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Código de resgate inválido ou já utilizado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})

def processar_imagem_qr_code(request):
    """Processa upload de imagem de QR code com correção de espelhamento"""
    try:
        from pyzbar.pyzbar import decode
        import cv2
        import numpy as np
        from PIL import Image
        import tempfile
        import os
        
        qr_image = request.FILES['qr_image']
        
        # Salvar imagem temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            for chunk in qr_image.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            # Ler QR code com correção de espelhamento
            qr_data = ler_qr_code_com_espelhamento(temp_path)
            
            if qr_data:
                # Processar os dados do QR code
                request.POST = request.POST.copy()
                request.POST['qr_data'] = qr_data
                return processar_dados_qr_code(request)
            else:
                return JsonResponse({'success': False, 'error': 'QR Code não pode ser lido. Tente novamente.'})
                
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except ImportError:
        return JsonResponse({'success': False, 'error': 'Funcionalidade de upload de imagem não disponível'})
    except Exception as e:
        print(f"ERRO no processamento de imagem: {e}")
        return JsonResponse({'success': False, 'error': f'Erro ao processar imagem: {str(e)}'})

def ler_qr_code_com_espelhamento(image_path):
    """Lê QR code tentando várias orientações incluindo espelhamento"""
    try:
        from pyzbar.pyzbar import decode
        import cv2
        import numpy as np
        
        # Carregar imagem
        image = cv2.imread(image_path)
        
        if image is None:
            print("Erro: Não foi possível carregar a imagem")
            return None
        
        # Lista de transformações para tentar
        transformacoes = [
            ('original', image),
            ('espelhado_horizontal', cv2.flip(image, 1)),
            ('espelhado_vertical', cv2.flip(image, 0)),
            ('espelhado_ambos', cv2.flip(image, -1)),
            ('rotacionado_90', cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)),
            ('rotacionado_180', cv2.rotate(image, cv2.ROTATE_180)),
            ('rotacionado_270', cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)),
        ]
        
        # Tentar cada transformação
        for nome, img_transformada in transformacoes:
            try:
                # Tentar decodificar
                decoded_objects = decode(img_transformada)
                
                if decoded_objects:
                    qr_data = decoded_objects[0].data.decode('utf-8')
                    print(f"QR Code lido com transformação: {nome}")
                    print(f"Dados: {qr_data}")
                    
                    # Verificar se é um formato válido
                    if qr_data.startswith('promocao:'):
                        return qr_data
                    
            except Exception as e:
                print(f"Erro na transformação {nome}: {e}")
                continue
        
        print("Nenhuma transformação funcionou")
        return None
        
    except Exception as e:
        print(f"Erro geral no processamento: {e}")
        return None

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