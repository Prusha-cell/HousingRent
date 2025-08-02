from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile


# Этот код автоматически создаёт профиль пользователя (UserProfile) сразу после того,
# как в базе появился новый объект User.
@receiver(post_save, sender=User)                   # параметр sender=User - значит, что наш обработчик будет
def create_profile(sender, instance, created, **kwargs):  # срабатывать только когда сохраняется объект класса User,
    if created:                                           # а не любая другая модель.
        UserProfile.objects.create(user=instance)         # Параметр instance — это только что сохранённый пользователь.
                                                          # Параметр created — булево значение: True, если объект был
                                                          # создан, а не просто обновлён. Если created == True,
                                                          # внутри блока создаётся новый UserProfile, привязанный
                                                          # к этому User через поле user=instance.



