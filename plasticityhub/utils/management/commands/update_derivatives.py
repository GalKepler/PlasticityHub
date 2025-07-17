import os
from pathlib import Path
from typing import Union

import environ
import pandas as pd
import tqdm
from crontab import CronTab
from django.core.management.base import BaseCommand
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from plasticityhub.scans.models import Session

CSV_OUTPUT_FILE = "sessions_with_derivatives.csv"
BIDS_PATH = Path("/mnt/62/Bids")
DERIVATIVES_PATH = Path("/mnt/62/Processed_Data/derivatives/")


def output_to_csv_with_derivatives(
    output_path: str = CSV_OUTPUT_FILE,
    bids_path=BIDS_PATH,
    derivatives_path=DERIVATIVES_PATH,
):
    """
    Output all sessions and some relevant information to a CSV file.

    Parameters
    ----------
    output_path : str
        The path to the output CSV file.
    bids_path : Path
        The path to the BIDS directory.
    derivatives_path : Path
        The path to the derivatives directory.
    """
    sessions = Session.objects.all()
    df = pd.DataFrame(
        index=range(len(sessions)),
        columns=[
            "subject_code",
            "session_id",
            "study",
            "group",
            "condition",
            "rawdata",
            "bids",
            "keprep",
            "kepost",
        ],
    )
    for i, session in tqdm.tqdm(
        enumerate(sessions), total=len(sessions), desc="Sessions"
    ):
        subject_code = session.subject.subject_code
        session_id = session.session_id
        df.loc[i, "subject_code"] = subject_code
        df.loc[i, "session_id"] = session_id
        df.loc[i, "study"] = session.study.name
        df.loc[i, "group"] = session.group.name
        df.loc[i, "condition"] = session.condition.name
        df.loc[i, "rawdata"] = session.rawdata_path
        subject_addition = (
            subject_code.replace("_", "")
            .replace(" ", "")
            .replace("\t", "")
            .replace("-", "")
        )
        bids = bids_path / f"sub-{subject_addition}" / f"ses-{session_id}"
        if bids.exists():
            df.loc[i, "bids"] = bids
        for sub_dir in ["keprep", "kepost", "freesurfer", "CAT12.9_2577"]:
            if sub_dir != "freesurfer":
                dest = (
                    derivatives_path
                    / sub_dir
                    / f"sub-{subject_addition}"
                    / f"ses-{session_id}"
                )
            else:
                dest = derivatives_path / sub_dir / f"sub-{subject_addition}"
            if dest.exists():
                df.loc[i, sub_dir] = dest

    df.to_csv(output_path)
    print(f"Output to {output_path}")
    return output_path


def google_authenticate(authorized_user: str, force_new: bool = False):
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
    gauth.LoadCredentialsFile(authorized_user)
    # Check whether the credentials are expired
    if gauth.access_token_expired or force_new:
        print("Google credentials are expired or not found.")  # noqa: T201
        print("Authenticating with Google...")  # noqa: T201
        # Authenticate if credentials are not there
        # gauth.LocalWebserverAuth()
        gauth.CommandLineAuth()
        gauth.SaveCredentialsFile(authorized_user)
    else:
        # Initialize the saved credentials
        gauth.LoadCredentialsFile(authorized_user)
        gauth.Authorize()
    # Save the current credentials to a file for future use
    gauth.SaveCredentialsFile(authorized_user)
    return gauth


def upload_to_drive(
    file: Union[str, Path],
    folder_id: str,
    credentials: Union[str, Path],
):
    """
    Upload a file to Google Drive

    Parameters
    ----------
    file : Union[str, Path]
        File to upload
    folder_id : str, optional
        Folder ID in Google Drive, by default FOLDER_ID
    credentials : Union[str, Path], optional
        Path to the credentials file, by default CREDENTIALS
    """
    # gauth = GoogleAuth()
    # gauth.LoadCredentialsFile(credentials)
    gauth = google_authenticate(credentials)
    drive = GoogleDrive(gauth)

    file_name = Path(file).name

    # delete existing file in drive
    file_list = drive.ListFile(
        {"q": f"title='{file_name}' and '{folder_id}' in parents and trashed=false"}
    ).GetList()
    for file_to_delete in file_list:
        drive.CreateFile({"id": file_to_delete["id"]}).Delete()
        print("File deleted from Google Drive")

    file_to_upload = drive.CreateFile(
        {"title": file_name, "parents": [{"id": folder_id}]}
    )
    file_to_upload.SetContentFile(file)
    file_to_upload.Upload()
    print("File uploaded to Google Drive")


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)
    folder_id = env("GOOGLE_DRIVE_FOLDER_ID", default=None)

    def handle(self, *args, **kwargs):
        out_file = output_to_csv_with_derivatives()
        upload_to_drive(out_file, self.folder_id, self.authorized_user)
        print("Done.")
