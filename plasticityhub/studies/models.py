from django.db import models


class Lab(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Study(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    lab = models.ManyToManyField(Lab, related_name="studies")

    def __str__(self):
        return self.name


class Group(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="groups",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Condition(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="conditions",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
