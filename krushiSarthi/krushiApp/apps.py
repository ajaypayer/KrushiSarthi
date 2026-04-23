from django.apps import AppConfig


class KrushiappConfig(AppConfig):
    name = 'krushiApp'

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'krushiApp'

    def ready(self):
        import krushiApp.signals