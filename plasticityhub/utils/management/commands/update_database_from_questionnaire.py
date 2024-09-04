import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand

from plasticityhub.behavioral.questionnaire import QuestionnaireResponse
from plasticityhub.scans.models import Session
from plasticityhub.subjects.models import Subject
from plasticityhub.utils.management.static.questionnaire_mapping import (
    COLUMNS_MAPPING,
    QUESTIONNAIRE_MAPPING,
)


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
    for col, mapping in QUESTIONNAIRE_MAPPING.items():
        if col not in df.columns:
            continue
        mapper = mapping.get("mapper")  # type: ignore[attr-defined]
        if mapper:
            df[col] = df[col].replace(mapper)
    return df


def load_data_from_sheet(
    sheet_key: str,
    credentials: str,
    authorized_user: str,
) -> pd.DataFrame:
    """
    Load the data from a Google Sheet.

    Parameters
    ----------
    sheet_key : str
        The Google Sheet Key.
    credentials : str
        The path to the credentials file.
    authorized_user : str
        The authorized user email.

    Returns
    -------
    pd.DataFrame
        The data from the Google Sheet.
    """
    gc_kwargs = {}
    if credentials:
        gc_kwargs["credentials_filename"] = credentials
    if authorized_user:
        gc_kwargs["authorized_user_filename"] = authorized_user
    gc = gs.oauth(**gc_kwargs)  # type: ignore[arg-type]
    sheet = gc.open_by_key(sheet_key)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])


def make_questionnaire_response(subject: Subject, row: pd.Series):
    """
    Create a QuestionnaireResponse object from a row in the DataFrame.

    Parameters
    ----------
    row : pd.Series
        The row to process.

    Returns
    -------
    QuestionnaireResponse
        The QuestionnaireResponse object.
    """
    questionnaire_response, _ = QuestionnaireResponse.objects.get_or_create(
        subject=subject,
        full_response=row.to_dict(),
    )
    return questionnaire_response


def update_sessions(subject: Subject, questionnaire_response: QuestionnaireResponse):
    """
    Update the sessions with the questionnaire response.

    Parameters
    ----------
    subject : Subject
        The subject associated with the questionnaire response.
    questionnaire_response : QuestionnaireResponse
        The questionnaire response to associate with the sessions.
    """
    for session in subject.sessions.all():
        if session.questionnaire_response is None:
            session.questionnaire_response = questionnaire_response
            session.time_between_questionnaire_and_scan = (  # type: ignore[attr-defined]
                session.timestamp - questionnaire_response.timestamp
            )
            session.save()
        else:
            # check to see if the current response is closer in time to the session
            if (
                session.questionnaire_response.timestamp
                and questionnaire_response.timestamp
                and abs(session.questionnaire_response.timestamp - session.timestamp)
                > abs(questionnaire_response.timestamp - session.timestamp)
            ):
                session.questionnaire_response = questionnaire_response
                session.time_between_questionnaire_and_scan = (  # type: ignore[attr-defined]
                    session.timestamp - questionnaire_response.timestamp
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
    subject_code = row.get("subject.code")
    subjects = Subject.objects.filter(subject_code=subject_code)
    if not subjects.exists():
        print(f"Subject with ID {row.get('subject.code')} not found")
        return
    if subjects.count() > 1:
        print(f"Multiple subjects with ID {row.get('subject.code')} found")
        return
    subject = subjects.first()
    questionnaire_response = make_questionnaire_response(subject, row)  # type: ignore[arg-type]
    subject.questionnaire_responses.add(questionnaire_response)  # type: ignore[union-attr]
    update_sessions(subject, questionnaire_response)  # type: ignore[arg-type]


def update_database_from_sheet(sheet_key: str, credentials: str, authorized_user: str):
    """
    Update the database with information from a Google Sheet.

    Parameters
    ----------
    sheet_key : str
        The Google Sheet Key.
    credentials : str
        The path to the credentials file.
    authorized_user : str
        The authorized user email.
    """
    # Load the data from the Google Sheet
    q_df = load_data_from_sheet(
        sheet_key,
        credentials,
        authorized_user,
    )
    # Reformat the DataFrame
    q_df = reformat_df(q_df)

    # Update the database with the information from the DataFrame
    for i, row in tqdm.tqdm(q_df.iterrows()):
        try:
            process_row(row)
        except Exception as e:  # noqa: BLE001
            print(f"\nError processing row {i}: {row}")  # noqa: T201
            print(e)  # noqa: T201


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    sheet_key = env("QUESTIONNAIRE_SHEET_KEY", default=None)
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)

    def add_arguments(self, parser):
        parser.add_argument(
            "sheet_key",
            nargs="?",
            type=str,
            help="Google Sheet Key",
            default=self.sheet_key,
        )
        parser.add_argument(
            "credentials",
            type=str,
            nargs="?",
            help="Path to the credentials file",
            default=self.credentials,
        )
        parser.add_argument(
            "authorized_user",
            type=str,
            nargs="?",
            help="Authorized user email",
            default=self.authorized_user,
        )

    def handle(self, *args, **kwargs):
        sheet_key = kwargs["sheet_key"]
        credentials = kwargs["credentials"]
        authorized_user = kwargs["authorized_user"]
        update_database_from_sheet(sheet_key, credentials, authorized_user)
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
