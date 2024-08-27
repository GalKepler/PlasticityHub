from pathlib import Path

import pandas as pd
import tqdm

from plasticityhub.scans.models import Session
from plasticityhub.studies.models import Condition
from plasticityhub.studies.models import Group
from plasticityhub.studies.models import Lab
from plasticityhub.studies.models import Study
from plasticityhub.subjects.models import Subject

COLUMNS_MAPPING = {
    "first_name": {
        "scope": "subject",
        "field": "first_name",
    },
    "last_name": {
        "scope": "subject",
        "field": "last_name",
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

    # Split the name into first, middle, and last name components.
    # keep only the first and last name components
    name_components = pd.DataFrame(index=df.index, columns=["first_name", "last_name"])
    for i, row in df.iterrows():
        try:
            name_parts = row["name"].split()
        except AttributeError:
            name_parts = ["Unknown", "Unknown"]
        name_components.loc[i, "first_name"] = name_parts[0]
        name_components.loc[i, "last_name"] = name_parts[-1]

    # Concatenate the name components with the original data
    df = pd.concat([df, name_components], axis=1)  # noqa: PD901
    return df  # noqa: RET504


def update_database_from_file(in_file: Path):
    """
    Update the database with information from a CSV file.

    Parameters
    ----------
    in_file : Path
        The path to the input CSV file containing the data to update the database with.
    """
    # Read the data from the input file
    df = pd.read_csv(in_file)  # noqa: PD901

    # Reformat the DataFrame
    df = reformat_df(df)  # noqa: PD901

    # Update the database with the information from the DataFrame
    for _, row in tqdm.tqdm(df.iterrows()):
        subject_kwargs = {}
        session_kwargs = {}
        for col, mapping in COLUMNS_MAPPING.items():
            if mapping["scope"] == "subject":
                subject_kwargs[mapping["field"]] = row[col]
            elif mapping["scope"] == "session":
                session_kwargs[mapping["field"]] = row[col]
        subject, _ = Subject.objects.get_or_create(**subject_kwargs)
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
