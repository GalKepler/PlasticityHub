import datetime

import pandas as pd
from django.db import models

from plasticityhub.subjects.models import Subject


class SECAMeasurement(models.Model):
    SECA_SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("U", "Unknown"),
    ]
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="seca_measurements",
        help_text="The subject associated with this measurement",
    )
    full_measurement = models.JSONField(
        help_text="The measurement from the SECA scale",
    )
    timestamp = models.DateTimeField(
        help_text="The timestamp of the measurement",
        editable=False,
        null=True,
    )
    date = models.DateField(
        help_text="The date of the measurement",
        editable=False,
        null=True,
    )
    time = models.TimeField(
        help_text="The time of the measurement",
        editable=False,
        null=True,
    )
    date_of_birth = models.DateField(
        help_text="The date of birth of the subject",
        editable=False,
        null=True,
    )
    sex = models.CharField(max_length=1, choices=SECA_SEX_CHOICES, default="U")
    subject_code = models.CharField(
        max_length=50,
        help_text="The subject code associated with the measurement",
        blank=True,
        null=True,
    )
    bmi = models.FloatField(
        help_text="The BMI of the subject",
        editable=False,
        null=True,
    )
    weight = models.FloatField(
        help_text="The weight of the subject",
        editable=False,
        null=True,
    )
    height = models.FloatField(
        help_text="The height of the subject",
        editable=False,
        null=True,
    )

    def __str__(self):
        return f"{self.subject} - SECA Measurement"

    class Meta:
        verbose_name = "SECA Measurement"
        verbose_name_plural = "SECA Measurements"

    def save(self, *args, **kwargs):
        self.timestamp = self.infer_timestamp()
        self.date = self.timestamp.date()
        self.time = self.timestamp.time()
        self.date_of_birth = self.infer_date_of_birth()
        self.sex = self.infer_sex()
        self.subject_code = self.infer_subject_code()
        self.bmi = self.infer_bmi()
        self.weight = self.infer_weight()
        self.height = self.infer_height()
        super().save(*args, **kwargs)

    def infer_timestamp(self) -> datetime.datetime:
        """
        Infer the timestamp of the measurement from the full measurement data.

        Returns
        -------
        datetime.datetime
            The timestamp of the measurement
        """
        return datetime.datetime.strptime(
            self.full_measurement.get("timestamp"), "%d/%m/%Y"
        ).astimezone()

    def infer_date_of_birth(self) -> datetime.datetime:
        """
        Infer the date of birth of the subject from the full measurement data.

        Returns
        -------
        datetime.datetime
            The date of birth of the subject
        """
        return datetime.datetime.strptime(
            self.full_measurement.get("date of birth"), "%d/%m/%Y"
        ).astimezone()

    def infer_sex(self) -> str:
        """
        Infer the sex of the subject from the full measurement data.

        Returns
        -------
        str
            The sex of the subject
        """
        return self.full_measurement.get("gender").capitalize()[0]

    def infer_subject_code(self) -> str:
        """
        Infer the subject code from the full measurement

        Returns
        -------
        str
            The subject code
        """
        return self.full_measurement.get("subject_code")

    def infer_bmi(self) -> float:
        """
        Infer the BMI of the subject from the full measurement data.

        Returns
        -------
        float
            The BMI of the subject
        """
        return float(self.full_measurement.get("bmi"))

    def infer_weight(self) -> float:
        """
        Infer the weight of the subject from the full measurement data.

        Returns
        -------
        float
            The weight of the subject
        """
        return float(self.full_measurement.get("weight"))

    def infer_height(self) -> float:
        """
        Infer the height of the subject from the full measurement data.

        Returns
        -------
        float
            The height of the subject
        """
        return float(self.full_measurement.get("height"))
