from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import login, logout
from .forms import ClienteRegistrationForm, ComercianteRegistrationForm
from .models import CustomUser

def register_cliente(request):
    if request.method == 'POST':
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_confirmation_email(request, user)
            messages.success(request, 'Por favor, confirme seu email para completar o cadastro.')
            return redirect('login')
    else:
        form = ClienteRegistrationForm()
    return render(request, 'accounts/register_cliente.html', {'form': form})

def register_comerciante(request):
    if request.method == 'POST':
        form = ComercianteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_confirmation_email(request, user)
            messages.success(request, 'Por favor, confirme seu email para completar o cadastro.')
            return redirect('login')
    else:
        form = ComercianteRegistrationForm()
    return render(request, 'accounts/register_comerciante.html', {'form': form})

def send_confirmation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    confirm_url = request.build_absolute_uri(
        reverse('confirm_email', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Confirme seu cadastro no Sistema de Fidelidade'
    html_message = render_to_string('accounts/email_confirmation.html', {
        'user': user,
        'confirm_url': confirm_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def confirm_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.email_confirmado = True
        user.save()
        messages.success(request, 'Email confirmado com sucesso! Você já pode fazer login.')
        return redirect('login')
    else:
        messages.error(request, 'Link de confirmação inválido ou expirado.')
        return redirect('home')

def custom_logout(request):
    logout(request)
    return redirect('login')