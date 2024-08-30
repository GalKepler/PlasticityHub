import datetime

from django.db import models

from plasticityhub.behavioral.questionnaire import QuestionnaireResponse
from plasticityhub.studies.models import Condition, Group, Lab, Study
from plasticityhub.subjects.models import Subject


class Session(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The subject associated with this session",
    )
    # The following fields are related to the questionnaire
    questionnaire_response = models.ForeignKey(
        QuestionnaireResponse,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The questionnaire response associated with this session",
        null=True,
    )
    time_between_scan_and_questionnaire = models.DurationField(
        help_text="The time between the scan and the questionnaire",
        blank=True,
        null=True,
    )

    # The following fields are related to the study
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
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The lab associated with this session",
        null=True,
    )
    scan_tag = models.CharField(
        max_length=20,
        help_text="The tag associated with the scan (e.g, pre, post, during)",
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        help_text="The status of the session (e.g., complete, incomplete, canceled)",
        blank=True,
    )
    origin_session_id = models.CharField(
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
    timestamp = models.DateTimeField(editable=False, null=True)

    class Meta:
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
        ordering = ["timestamp"]

    def __str__(self):
        return f"Session {self.id} for {self.subject} on {self.date} at {self.time}"

    def save(self, *args, **kwargs):
        # Automatically set the inferred_datetime field
        self.timestamp = self.inferred_datetime
        super().save(*args, **kwargs)

    @property
    def inferred_datetime(self):
        """
        Return the datetime of the session based on the session
        """
        return datetime.datetime.strptime(
            self.origin_session_id, "%Y%m%d_%H%M"
        ).astimezone()

    @property
    def date(self):
        """
        Return the date of the session
        """
        return self.inferred_datetime.date()

    @property
    def time(self):
        """
        Return the time of the session
        """
        return self.inferred_datetime.time()

    @property
    def session_id(self):
        """
        Return the raw session ID
        """
        return datetime.datetime.strftime(self.inferred_datetime, format="%Y%m%d%H%M")
