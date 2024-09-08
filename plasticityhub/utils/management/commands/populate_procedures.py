from pathlib import Path

import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand

from plasticityhub.procedures.models import Procedure
from plasticityhub.scans.models import Session
from plasticityhub.studies.models import Condition, Group, Lab, Study
from plasticityhub.subjects.models import Subject
from plasticityhub.utils.management.static.database_mapping import COLUMNS_MAPPING
from plasticityhub.utils.management.static.procedures.utils import parse_session


def populate_kepost_procedures(qnap_path: str, overwrite: bool = False):
    """
    Populate the database with the properties of existing procedures.
    """
    qnap_path = Path(qnap_path)
    for session in tqdm.tqdm(Session.objects.all()):
        kepost_output = list(
            qnap_path.glob(
                f"share/Biden_Results/derivatives/kepost/sub-*/ses-{session.session_id}"
            )
        )
        if not kepost_output:
            continue
        kepost_output = kepost_output[0]
        procedure, created = Procedure.objects.get_or_create(
            session=session,
            name="kepost",
            path=kepost_output,
        )
        if created or overwrite:
            procedure.outputs = parse_session(kepost_output)
            procedure.save()


class Command(BaseCommand):
    help = "Populate the database with the properties of existing procedures."
    env = environ.Env()
    qnap_path = env.get_value("QNAP_PATH")

    def add_arguments(self, parser):
        parser.add_argument(
            "--qnap_path",
            type=str,
            default=self.qnap_path,
            help="The path to the QNAP directory.",
        )
        # whether to overwrite existing procedures with new outputs
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Whether to overwrite existing procedures with new outputs.",
        )

    def handle(self, *args, **kwargs):
        qnap_path = kwargs.get("qnap_path")
        overwrite = kwargs.get("overwrite")
        populate_kepost_procedures(qnap_path, overwrite)
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
