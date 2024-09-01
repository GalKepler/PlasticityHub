import datetime

import pandas as pd
from django.db import models

from plasticityhub.subjects.models import Subject


class SECAMeasurement(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="seca_measurements",
        help_text="The subject associated with this measurement",
    )
    full_measurement = models.JSONField(
        help_text="The measurement from the SECA scale",
    )

    def __str__(self):
        return f"{self.subject} - SECA Measurement"

    class Meta:
        verbose_name = "SECA Measurement"
        verbose_name_plural = "SECA Measurements"

    @property
    def timestamp(self):
        return datetime.datetime.strptime(
            self.full_measurement.get("timestamp"), "%d/%m/%Y"
        ).astimezone()

    @property
    def date_of_birth(self):
        return datetime.datetime.strptime(
            self.full_measurement.get("date of birth"), "%d/%m/%Y"
        ).astimezone()

    @property
    def sex(self):
        return self.full_measurement.get("gender").capitalize()[0]

    @property
    def subject_code(self):
        return self.full_measurement.get("subject_code")
