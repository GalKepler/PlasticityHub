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

# def collect_results()


class Command(BaseCommand):
    help = "Populate the database with the properties of existing procedures."
    env = environ.Env()

    def add_arguments(self, parser):
        parser.add_argument(
            "--destination",
            type=str,
            help="The path to store the output files.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Whether to overwrite existing files.",
        )

    def handle(self, *args, **kwargs):
        destination = kwargs.get("destinaiton")
        overwrite = kwargs.get("overwrite")
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
