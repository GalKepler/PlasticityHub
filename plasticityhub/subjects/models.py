from django.db import models
from django.utils import timezone


class Subject(models.Model):
    SUBJECT_SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("U", "Unknown"),
    ]

    SUBJECT_HANDEDNESS_CHOICES = [
        ("R", "Right"),
        ("L", "Left"),
        ("A", "Ambidextrous"),
        ("U", "Unknown"),
    ]

    subject_id = models.CharField(
        max_length=50,
        help_text="Unique identifier for the subject",
        unique=True,
    )
    subject_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unique identifier for questionnaires",
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the subject",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    sex = models.CharField(max_length=1, choices=SUBJECT_SEX_CHOICES, default="U")
    handedness = models.CharField(
        max_length=1,
        choices=SUBJECT_HANDEDNESS_CHOICES,
        default="U",
    )
    email = models.EmailField(
        blank=True,
        help_text="Email address for the subject",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for the subject",
    )
    status = models.CharField(
        max_length=20,
        blank=True,
        help_text="Status of the subject",
    )
    height = models.FloatField(
        blank=True,
        null=True,
        help_text="Height of the subject in centimeters",
    )
    weight = models.FloatField(
        blank=True,
        null=True,
        help_text="Weight of the subject in kilograms",
    )
    age = models.IntegerField(
        blank=True,
        null=True,
        help_text="Age of the subject",
    )
    comments = models.TextField(
        blank=True,
        help_text="Additional comments or notes about the subject",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["subject_id"]

    def __str__(self):
        return f"{self.subject_id} - {self.first_name} {self.last_name or ''}".strip()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def calculate_age(self):
        """
        Calculate the age of the subject based on the date of birth.

        Returns
        -------
        int or None
            The age of the subject in years, or None if the date of birth is not
        """
        if self.date_of_birth:
            today = timezone.now().date()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None

    def get_age(self):
        return self.calculate_age()

    def calculate_bmi(self):
        """
        Calculate the body mass index (BMI)
        of the subject based on the height and weight.
        BMI = weight (kg) / height (m)^2

        Returns
        -------
        float or None
            The body mass index (BMI) of the subject,
            or None if the height or weight is not available
        """
        if self.height and self.weight:
            return self.weight / ((self.height / 100) ** 2)
        return None

    @property
    def first_name(self):
        return self.name.split()[0]

    @property
    def last_name(self):
        return " ".join(self.name.split()[1:])

    @property
    def bmi(self):
        return self.calculate_bmi()
