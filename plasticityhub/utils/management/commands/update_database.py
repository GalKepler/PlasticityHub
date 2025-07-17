import json
import os

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
from plasticityhub.utils.management.static.questionnaire_mapping import (
    QUESTIONNAIRE_MAPPING,
)

REMOTE_MOUNTS = {"/mnt/62": "\\132.66.46.62", "/mnt/snbb": "\\132.66.46.165"}
CSV_OUTPUT_FILE = "sessions.csv"
QUETIONNAIRE_KEYS = [
    "PI006",
    # "PI004",
    # "PI005",
    "PI007",
    "PI012",
    "PI002",
    "PI013",
    "PI014",
    "LS005",
    "SE001",
    "SE008",
    "SE010",
    "SE011",
    "SE012",
]


def gather_questionnaire_data(session: Session):
    """
    Gather the questionnaire data from the session.

    Parameters
    ----------
    session : Session
        The session to gather the data.
    """
    questionnaire = session.questionnaire_response
    if questionnaire is None:
        return {}
    result = {}
    for key in QUETIONNAIRE_KEYS:
        field = QUESTIONNAIRE_MAPPING.get(key).get("field")
        if field:
            result[field] = questionnaire.full_response.get(key)
    return result


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
    df["gender"] = df["gender"].apply(lambda x: x[0].upper() if x else "U")

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
    subject = Subject.objects.filter(
        subject_id=subject_kwargs["subject_id"],
        subject_code=subject_kwargs["subject_code"],
    ).first()
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


def validate_existing_session(session_kwargs: dict):
    """
    Check if the session is unique based on the provided information.
    If it exists, make sure all the information is the same.
    If the information is different, delete the existing session and create a new one.

    Parameters
    ----------
    session_kwargs : dict
        The keyword arguments to create the session.

    Returns
    -------
    bool
        True if the session is unique, False otherwise.
    """
    existing_session = Session.objects.filter(
        origin_session_id=session_kwargs["origin_session_id"]
    ).first()
    if not existing_session:
        return True
    for key, value in session_kwargs.items():
        if getattr(existing_session, key) != value:
            print(
                f"Deleting session {existing_session.session_id} due to {key} mismatch."
            )
            existing_session.delete()
            return True
    return False


def process_row(row: pd.Series, mapped_rawdata: dict):
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
    _ = validate_existing_session(session_kwargs)
    session, _ = Session.objects.get_or_create(**session_kwargs)
    rawdata_path = mapped_rawdata.get(session.origin_session_id)
    if rawdata_path:
        # for local_mount, remote_mount in REMOTE_MOUNTS.items():
        #     rawdata_path = rawdata_path.replace(local_mount, remote_mount)
        session.rawdata_path = rawdata_path
    session.save()


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


def load_mapped_rawdata(mapped_rawdata_path: str) -> dict:
    """
    Load the mapped rawdata from a file.

    Parameters
    ----------
    mapped_rawdata_path : str
        The path to the mapped rawdata file.

    Returns
    -------
    dict
        The mapped rawdata.
    """
    with open(mapped_rawdata_path, "r") as f:
        mapped_rawdata = json.load(f)
    return mapped_rawdata


def update_database_from_sheet(
    sheet_key: str, credentials: str, authorized_user: str, mapped_rawdata_path: str
):
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

    # Load the mapped rawdata
    mapped_rawdata = load_mapped_rawdata(mapped_rawdata_path)
    # Update the database with the information from the DataFrame
    for i, row in tqdm.tqdm(crf_df.iterrows()):
        try:
            process_row(row, mapped_rawdata)
        except Exception as e:  # noqa: BLE001
            print(f"\nError processing row {i}:\n")  # noqa: T201
            print(f"name: {row['name']}")
            print(f"scanid: {row['scanid']}")
            print(f"Error: {e}")  # noqa: T201
            if "date" in e.args[0]:
                raise e


def output_to_csv(output_path: str = CSV_OUTPUT_FILE):
    """
    Output all sessions and some relevant information to a CSV file.

    Parameters
    ----------
    output_path : str
        The path to the output CSV file.
    """
    sessions = Session.objects.all()
    df = pd.DataFrame(
        index=range(len(sessions)),
        columns=[
            "subject_code",
            "subject_id",
            "dob",
            "age_at_scan",
            "sex",
            "session_id",
            "study",
            "group",
            "condition",
            "path",
        ],
    )
    for i, session in enumerate(sessions):
        for key, value in zip(
            [
                "subject_code",
                "subject_id",
                "dob",
                "age_at_scan",
                "sex",
                "weight",
                "height",
                "session_id",
                "study",
                "group",
                "condition",
                "path",
            ],
            [
                session.subject.subject_code,
                session.subject.subject_id,
                session.subject.date_of_birth,
                session.age_at_scan,
                session.subject.sex,
                session.subject.weight,
                session.subject.height,
                session.session_id,
                session.study.name,
                session.group.name,
                session.condition.name,
                session.rawdata_path,
            ],
            strict=False,
        ):
            df.loc[i, key] = value
        # df.loc[i] = [
        #     session.subject.subject_code,
        #     session.subject.subject_id,
        #     session.subject.date_of_birth,
        #     session.age_at_scan,
        #     session.subject.sex,
        #     session.session_id,
        #     session.study.name,
        #     session.group.name,
        #     session.condition.name,
        #     session.rawdata_path,
        # ]
        for key, value in gather_questionnaire_data(session).items():
            df.loc[i, key] = value
    df["path"] = df["path"].replace("", pd.NA)
    df.to_csv(output_path, index=False)
    os.system(
        f"rsync -azPL {output_path} yalab_dev@biden.tau.ac.il:/home/yalab_dev/yalab-devops"
    )


def output_to_csv_with_derivatives(output_path: str = CSV_OUTPUT_FILE):
    """
    Output all sessions and some relevant information to a CSV file.

    Parameters
    ----------
    output_path : str
        The path to the output CSV file.
    """
    sessions = Session.objects.all()
    df = pd.DataFrame(
        index=range(len(sessions)),
        columns=["subject_code", "session_id", "bids", "keprep", "kepost"],
    )
    for i, session in enumerate(sessions):
        df.loc[i] = [
            session.subject.subject_code,
            session.session_id,
            session.study.name,
            session.group.name,
            session.condition.name,
            session.rawdata_path,
        ]
    df["path"] = df["path"].replace("", pd.NA)
    df.to_csv(output_path, index=False)
    os.system(
        f"rsync -azPL {output_path} yalab_dev@biden.tau.ac.il:/home/yalab_dev/yalab-devops"
    )


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    sheet_key = env("CRF_SHEET_KEY", default=None)
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)
    mapped_rawdata_path = env("MAPPED_RAWDATA_PATH", default=None)

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
        parser.add_argument(
            "--mapped_rawdata_path",
            type=str,
            nargs="?",
            help="Path to the mapped rawdata file",
            default=self.mapped_rawdata_path,
        )

    def handle(self, *args, **kwargs):
        sheet_key = kwargs["sheet_key"]
        credentials = kwargs["credentials"]
        authorized_user = kwargs["authorized_user"]
        update_database_from_sheet(
            sheet_key, credentials, authorized_user, kwargs["mapped_rawdata_path"]
        )
        output_to_csv()
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
