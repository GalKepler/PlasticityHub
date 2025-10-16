import datetime

import pandas as pd
from django.db import models

from plasticityhub.subjects.models import Subject


class QuestionnaireResponse(models.Model):

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="questionnaire_responses",
        help_text="The subject associated with this questionnaire response",
    )
    full_response = models.JSONField(
        help_text="The response to the questionnaire",
    )

    class Meta:
        verbose_name = "Questionnaire Response"
        verbose_name_plural = "Questionnaire Responses"

    def __str__(self):
        return f"{self.subject} - Questionnaire"

    @property
    def timestamp(self):
        dt = self.full_response.get("QTimeStamp")
        if self.filled and dt != "":
            return datetime.datetime.strptime(dt, "%m/%d/%Y").astimezone()
        return None

    @property
    def filled(self):
        return self.full_response.get("Questionnaire") != "No"
