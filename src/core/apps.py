from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Correção de compatibilidade para Django 4.2 + Python 3.14.
        # Centralizado no ready() do app core, para que seja aplicado em todos os testes e na execução normal.
        from django.template.context import BaseContext

        def patched_copy(self):
            new_copy = self.__class__.__new__(self.__class__)
            new_copy.__dict__.update(self.__dict__)
            if hasattr(self, 'dicts'):
                new_copy.dicts = self.dicts[:]
            return new_copy

        BaseContext.__copy__ = patched_copy
