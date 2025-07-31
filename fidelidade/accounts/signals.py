from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser
from core.models import Cliente, Comercio

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.tipo_usuario == 'cliente':
            Cliente.objects.create(usuario=instance)
        elif instance.tipo_usuario == 'comerciante':
            Comercio.objects.create(usuario=instance)