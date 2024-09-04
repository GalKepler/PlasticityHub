from typing import Union

from django.db import models

from plasticityhub.scans.models import Session
from plasticityhub.utils.management.static.procedures.utils import parse_session


class Procedure(models.Model):
    """
    A procedure that can be performed on a subject.
    """

    name = models.CharField(
        max_length=255,
        help_text="The name of the procedure",
    )
    description = models.TextField(
        help_text="The description of the procedure",
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="procedures",
        help_text="The session associated with this procedure",
    )
    path = models.CharField(
        max_length=255,
        help_text="The path to the procedure's output",
    )
    status = models.CharField(
        max_length=255,
        help_text="The status of the procedure",
        choices=[
            ("completed", "Completed"),
            ("in_progress", "In Progress"),
            ("not_started", "Not Started"),
        ],
    )
    outputs = models.JSONField(
        help_text="The outputs of the procedure",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the procedure was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the procedure was last updated",
    )

    class Meta:
        verbose_name = "Procedure"
        verbose_name_plural = "Procedures"

    def __str__(self):
        return f"{self.name} - {self.status} for Session {self.session.session_id}"

    def get(
        self, key: Union[str, dict], return_multiple: bool = False
    ) -> Union[dict, list]:
        """
        Get the value of a key in the outputs.

        Parameters
        ----------
        key : Union[str, dict]
            The key to retrieve.
        return_multiple : bool, optional
            Whether to return multiple values, by default False
        Returns
        -------
        Union[dict, list]
            The value of the key in the outputs.
        """
        result = []
        if isinstance(key, str):
            return {
                entity: file_path for file_path, entity in self.outputs.items()
            }.get(key)
        elif isinstance(key, dict):
            for file_path, entities in self.outputs.items():
                if all(
                    entity in entities and entities[entity] == value
                    for entity, value in key.items()
                ):
                    result.append(file_path)
                    if not return_multiple:
                        return result[0]
            return result
        else:
            raise NotImplementedError("Key must be a string or a dictionary.")
