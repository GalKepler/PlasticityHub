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

    def __str__(self):
        return f"{self.subject} - Questionnaire"

    class Meta:
        verbose_name = "Questionnaire Response"
        verbose_name_plural = "Questionnaire Responses"

    @property
    def timestamp(self):
        filled = self.full_response.get("Questionnaire")
        dt = self.full_response.get("QTimeStamp")
        if filled != "No":
            return datetime.datetime.strptime(dt, "%m/%d/%Y").astimezone()
        else:
            return None

    # @property
    # def sex(self):
    #     return self.full_response.get("sex")

    # @property
    # def height(self):
    #     return self.full_response.get("height")

    # @property
    # def weight(self):
    #     return self.full_response.get("weight")

    # @property
    # def version(self):
    #     return self.full_response.get("version")
