from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Запуск bot для тестирования'

    def handle(self, *args, **kwargs):
        if settings.DEBUG:
            from dragmetal.local_init import handle as handle_bot
        else:
            from dragmetal.webhook_init import handle as handle_bot
        handle_bot()
