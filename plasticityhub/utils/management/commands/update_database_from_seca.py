import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand

from plasticityhub.behavioral.questionnaire import QuestionnaireResponse
from plasticityhub.behavioral.seca import SECAMeasurement
from plasticityhub.scans.models import Session
from plasticityhub.subjects.models import Subject
from plasticityhub.utils.management.seca_mapping import COLUMNS_MAPPING, SECA_MAPPING


def reformat_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reformat the DataFrame to match the expected format for the database.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to reformat.

    Returns
    -------
    pd.DataFrame
        The reformatted DataFrame.
    """
    df.columns = df.columns.str.lower()
    df = df.rename(columns=COLUMNS_MAPPING)
    for col, mapping in SECA_MAPPING.items():
        if col not in df.columns:
            continue
        mapper = mapping.get("mapper")  # type: ignore[attr-defined]
        if mapper:
            df[col] = df[col].replace(mapper)
    return df


def make_seca_measurement(subject: Subject, row: pd.Series):
    """
    Create a SECAMeasurement object from a row in the DataFrame.

    Parameters
    ----------
    row : pd.Series
        The row to process.

    Returns
    -------
    SECAMeasurement
        The created SECAMeasurement object.
    """
    seca_measurement, _ = SECAMeasurement.objects.get_or_create(
        subject=subject,
        full_measurement=row.fillna("").to_dict(),
    )
    return seca_measurement


def update_sessions(subject: Subject, seca_measurement: SECAMeasurement):
    """
    Update the sessions with the questionnaire response.

    Parameters
    ----------
    subject : Subject
        The subject associated with the questionnaire response.
    seca_measurement : SECAMeasurement
        The SECA measurement to associate with the sessions.
    """
    for session in subject.sessions.all():
        if session.seca_measurement is None:
            session.seca_measurement = seca_measurement
            session.time_between_scan_and_seca = (  # type: ignore[attr-defined]
                session.timestamp - seca_measurement.timestamp
            )
            session.save()
        else:
            # check to see if the current response is closer in time to the session
            if (
                session.seca_measurement.timestamp
                and seca_measurement.timestamp
                and abs(session.seca_measurement.timestamp - session.timestamp)
                > abs(seca_measurement.timestamp - session.timestamp)
            ):
                session.seca_measurement = seca_measurement
                session.time_between_scan_and_seca = (  # type: ignore[attr-defined]
                    session.timestamp - seca_measurement.timestamp
                )
                session.save()


def process_row(row: pd.Series):
    """
    Process a row from the DataFrame.

    Parameters
    ----------
    row : pd.Series
        The row to process.
    """
    date_of_measurement = pd.to_datetime(row.get("timestamp"), format="%d/%m/%Y")
    date_of_birth = pd.to_datetime(row.get("date of birth"), format="%d/%m/%Y")
    sex = row.get("gender")[0]
    sessions = Session.objects.filter(
        date=date_of_measurement.date(),
        subject__date_of_birth=date_of_birth.date(),
        subject__sex=sex,
    )
    if not sessions.exists():
        print(f"Cound not find scanning session to associated with measurement:")
        print(f"date_of_measurement: {date_of_measurement}")
        print(f"date_of_birth: {date_of_birth}")
        print(f"subject's sex: {sex}\n")
        return
    if sessions.count() > 1:
        print(
            f"Found multiple scanning sessions to associated with measurement:\n{row}"
        )
        return
    session = sessions.first()
    subject = session.subject
    seca_measurement = make_seca_measurement(subject, row)  # type: ignore[arg-type]
    subject.seca_measurements.add(seca_measurement)  # type: ignore[union-attr]
    update_sessions(subject, seca_measurement)  # type: ignore[arg-type]


def update_database_from_file(file_path: str):
    """
    Update the database with information from a CSV file output from SECA.

    Parameters
    ----------
    file_path : str
        The path to the CSV file.
    """
    # Load the data from the Google Sheet
    seca_df = pd.read_csv(file_path)
    # Reformat the DataFrame
    seca_df = reformat_df(seca_df)

    # Update the database with the information from the DataFrame
    for i, row in tqdm.tqdm(seca_df.iterrows()):
        try:
            process_row(row)
        except Exception as e:  # noqa: BLE001
            print(f"\nError processing row {i}: {row}")  # noqa: T201
            print(e)


class Command(BaseCommand):
    help = "Update the database with information from a SECA CSV file."
    env = environ.Env()

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to the SECA CSV file",
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]
        update_database_from_file(file_path)
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
