import datetime

from django.db import models

from plasticityhub.studies.models import Condition
from plasticityhub.studies.models import Group
from plasticityhub.studies.models import Study
from plasticityhub.subjects.models import Subject


class Session(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The subject associated with this session",
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The study associated with this session",
        null=True,
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The group associated with this session",
        null=True,
    )
    condition = models.ForeignKey(
        Condition,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The condition associated with this session",
        null=True,
    )
    session_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier for the session",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or observations about the session",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
        ordering = ["session_id"]

    def __str__(self):
        return f"Session {self.id} for {self.subject} on {self.session_date}"

    @property
    def session_date(self):
        """
        Return the datetime of the session based on the session
        """
        return datetime.datetime.strptime(self.session_id, "%Y%m%d_%H%M").replace(
            tzinfo=datetime.UTC,
        )
