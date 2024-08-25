import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SubjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "subjects"
    verbose_name = _("Subjects")

    def ready(self):
        with contextlib.suppress(ImportError):
            import plasticityhub.subjects.signals  # noqa: F401
