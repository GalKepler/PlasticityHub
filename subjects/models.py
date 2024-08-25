from django.db import models


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
        unique=True,
        help_text="Unique identifier for the subject",
    )
    questionnaire_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unique identifier for the questionnaire",
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    sex = models.CharField(max_length=1, choices=SUBJECT_SEX_CHOICES, default="U")
    handedness = models.CharField(
        max_length=1,
        choices=SUBJECT_HANDEDNESS_CHOICES,
        default="U",
    )
    comments = models.TextField(
        blank=True,
        help_text="Additional comments or notes about the subject",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    studies = models.ManyToManyField(
        "studies.Study",
        related_name="subjects",
        blank=True,
        help_text="Studies that this subject is participating in",
    )
    groups = models.ManyToManyField(
        "studies.Group",
        related_name="subjects",
        blank=True,
        help_text="Groups that this subject is a member of",
    )
    conditions = models.ManyToManyField(
        "studies.Condition",
        related_name="subjects",
        blank=True,
        help_text="Conditions that this subject has been assigned to",
    )

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["subject_id"]

    def __str__(self):
        return f"{self.subject_id} - {self.first_name} {self.last_name or ''}".strip()
