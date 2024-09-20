import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand
from pydrive.auth import GoogleAuth

from plasticityhub.scans.models import Session
from plasticityhub.studies.models import Condition, Group, Lab, Study
from plasticityhub.subjects.models import Subject
from plasticityhub.utils.management.static.database_mapping import COLUMNS_MAPPING


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
    df.loc[:, "scanid"] = df.loc[:, "scanid"].replace("", pd.NA)
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

    # height - convert rows (where height is a number) to cm
    df["height"] = df["height"].apply(
        lambda x: x if x == "" else x if pd.isna(x) else float(x) * 100
    )
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
            latest_session = subject.sessions.order_by("-timestamp").first()
            if (
                latest_session
                and latest_session.origin_session_id
                > session_kwargs["origin_session_id"]
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
    subject.studies.add(study)
    subject.groups.add(group)
    subject.conditions.add(condition)
    subject.save()
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


def google_authenticate(
    credentials: str, authorized_user: str, force_new: bool = False
):
    """
    Authenticate with Google.

    Parameters
    ----------
    credentials : str
        The path to the credentials file.
    authorized_user : str
        The authorized user email.
    """
    # Authenticate and create the PyDrive client
    gauth = GoogleAuth()
    gauth.settings["client_config_file"] = credentials
    # Check whether the credentials are expired
    gauth.LoadCredentialsFile(authorized_user)
    if gauth.credentials is None or gauth.access_token_expired or force_new:
        print("Google credentials are expired or not found.")  # noqa: T201
        print("Authenticating with Google...")  # noqa: T201
        # Authenticate if credentials are not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved credentials
        gauth.Authorize()
    # Save the current credentials to a file for future use
    gauth.SaveCredentialsFile(authorized_user)


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
    # Authenticate with Google
    google_authenticate(credentials, authorized_user)
    gc_kwargs = {}
    if credentials:
        gc_kwargs["credentials_filename"] = credentials
    if authorized_user:
        gc_kwargs["authorized_user_filename"] = authorized_user
    try:
        gc = gs.oauth(**gc_kwargs)  # type: ignore[arg-type]
        sheet = gc.open_by_key(sheet_key)
    except Exception as e:  # noqa: BLE001
        print(f"Error loading the Google Sheet: {e}")  # noqa: T201
        gc = gs.oauth()
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
            print(f"\nError processing row {i}:\n")  # noqa: T201
            print(f"name: {row['name']}")
            print(f"scanid: {row['scanid']}")
            print(f"Error: {e}")  # noqa: T201
            if "date" in e.args[0]:
                raise e


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    sheet_key = env("CRF_SHEET_KEY", default=None)
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)

    def add_arguments(self, parser):
        parser.add_argument(
            "--sheet_key",
            nargs="?",
            type=str,
            help="Google Sheet Key",
            default=self.sheet_key,
        )
        parser.add_argument(
            "--credentials",
            type=str,
            nargs="?",
            help="Path to the credentials file",
            default=self.credentials,
        )
        parser.add_argument(
            "--authorized_user",
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
