import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand

from plasticityhub.scans.models import Session
from plasticityhub.studies.models import Condition
from plasticityhub.studies.models import Group
from plasticityhub.studies.models import Lab
from plasticityhub.studies.models import Study
from plasticityhub.subjects.models import Subject

COLUMNS_MAPPING = {
    "name": {
        "scope": "subject",
        "field": "name",
    },
    "dob": {
        "scope": "subject",
        "field": "date_of_birth",
    },
    "id": {
        "scope": "subject",
        "field": "subject_id",
    },
    "email": {
        "scope": "subject",
        "field": "email",
    },
    "cellular no.": {
        "scope": "subject",
        "field": "phone",
    },
    "gender": {
        "scope": "subject",
        "field": "sex",
    },
    "height": {
        "scope": "subject",
        "field": "height",
    },
    "weight": {
        "scope": "subject",
        "field": "weight",
    },
    "protocol": {
        "scope": "session",
        "field": "study",
    },
    "study": {
        "scope": "session",
        "field": "group",
    },
    "group": {
        "scope": "session",
        "field": "condition",
    },
    "lab": {
        "scope": "session",
        "field": "lab",
    },
    "scantag": {
        "scope": "session",
        "field": "scan_tag",
    },
    "qcode": {
        "scope": "subject",
        "field": "questionnaire_id",
    },
    "scanid": {
        "scope": "session",
        "field": "session_id",
    },
}


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
    # drop repeated scanid, keep the first one
    df = df.drop_duplicates(subset=["scanid"], keep="first")  # noqa: PD901
    # drop rows with missing scanid
    df = df.dropna(subset=["scanid"])  # noqa: PD901
    # Convert the date of birth to a datetime object
    df["dob"] = pd.to_datetime(df["dob"])

    # Pad the questionnaire and ID with leading zeros
    df["qcode"] = df["qcode"].astype(str).str.zfill(4)
    df["id"] = df["id"].astype(str).str.zfill(9)

    # Convert Sex to uppercase
    df["gender"] = df["gender"].apply(lambda x: x[0].upper())

    # Convert the protocol, study, and group to title case
    for col in ["protocol", "study", "group"]:
        df[col] = df[col].str.title()

    df["scantag"] = df["scantag"].str.lower()

    df["name"] = df["name"].str.title().fillna("Unknown Unknown")
    return df


def get_or_create_subject(subject_kwargs: dict, session_kwargs: dict):
    """
    Get or create a subject and session based on the provided information.

    Parameters
    ----------
    subject_kwargs : dict
        The keyword arguments to create the subject.
    session_kwargs : dict
        The keyword arguments to create the session.

    Returns
    -------
    Subject
        The subject object.
    Session
        The session object.
    """
    # check for existing subject
    subject = Subject.objects.filter(subject_id=subject_kwargs["subject_id"]).first()
    # if subject exists, update the subject
    if subject:
        for key, value in subject_kwargs.items():
            # check the existing attribute
            if getattr(subject, key) == value or (not value):
                continue
            # update only if the session is later than the latest session
            latest_session = subject.sessions.order_by("-session_id").first()
            if (
                latest_session
                and latest_session.session_id > session_kwargs["session_id"]
            ):
                # check if the attribute is empty
                if not getattr(subject, key):
                    setattr(subject, key, value)

                continue
            # update the attribute if value is not empty
            if value:
                setattr(subject, key, value)
        subject.save()
    else:
        subject, _ = Subject.objects.get_or_create(
            **{key: value for key, value in subject_kwargs.items() if value},
        )
    return subject


def process_row(row: pd.Series):
    """
    Process a row from the DataFrame and update the database with the information.

    Parameters
    ----------
    row : pd.Series
        The row to process.
    """
    subject_kwargs = {}
    session_kwargs = {}
    for col, mapping in COLUMNS_MAPPING.items():
        if mapping["scope"] == "subject":
            subject_kwargs[mapping["field"]] = row[col]
        elif mapping["scope"] == "session":
            session_kwargs[mapping["field"]] = row[col]

    subject = get_or_create_subject(subject_kwargs, session_kwargs)
    study, _ = Study.objects.get_or_create(name=session_kwargs["study"])
    group, _ = Group.objects.get_or_create(
        name=session_kwargs["group"],
        study=study,
    )
    condition, _ = Condition.objects.get_or_create(
        name=session_kwargs["condition"],
        study=study,
    )
    lab, _ = Lab.objects.get_or_create(name=session_kwargs["lab"])
    session_kwargs.update(
        {
            "subject": subject,
            "study": study,
            "group": group,
            "condition": condition,
            "lab": lab,
        },
    )
    session, _ = Session.objects.get_or_create(**session_kwargs)


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
    gc = gs.oauth(**gc_kwargs)
    sheet = gc.open_by_key(sheet_key)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])


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
    crf_df = load_data_from_sheet(
        sheet_key,
        credentials,
        authorized_user,
    )
    # Reformat the DataFrame
    crf_df = reformat_df(crf_df)

    # Update the database with the information from the DataFrame
    for i, row in tqdm.tqdm(crf_df.iterrows()):
        try:
            process_row(row)
        except Exception as e:  # noqa: BLE001
            print(f"\nError processing row {i}: {row}")  # noqa: T201
            print(e)  # noqa: T201
            break


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    sheet_key = env("CRF_SHEET_KEY", default=None)
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
