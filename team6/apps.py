from django.apps import AppConfig


class Team6Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'team6'

    def ready(self):
        # ثبت سیگنال‌ها
        import team6.signals
