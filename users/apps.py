from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # импортируем module signals, чтобы зарегистрировать receiver
        import users.signals
