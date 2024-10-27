import pickle
import warnings
from copy import deepcopy
from pathlib import Path
from typing import Optional

import environ
import gspread as gs
import pandas as pd
import tqdm
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from plasticityhub.procedures.models import Procedure
from plasticityhub.utils.management.static.procedures.kepost.outputs import (
    AVAILABLE_ATLASES,
    QC_PARAMETERS,
    TENSORS_PARAMETERS,
)

warnings.filterwarnings("ignore")


def add_atlases_to_queries(base_queries: list[dict], atlases: dict):
    """
    Add the atlases to the queries.

    Parameters
    ----------
    base_queries : list[dict]
        The queries to add the atlases.
    atlases : dict
        The atlases to add to the queries.
    """
    queries = []
    for query in base_queries:
        for atlas in atlases:
            updated_query = deepcopy(query)
            if "schaefer" in atlas:
                atlas_name = atlas.split("_")[0]
                density = atlas.split("_")[1]
                div = atlas.split("_")[2] + "networks"
                atlas_query = {"atlas": atlas_name, "den": density, "division": div}
            else:
                atlas_name = atlas
                atlas_query = {"atlas": atlas_name}
            updated_query["query"].update(atlas_query)
            updated_query["atlas"] = {atlas: atlases[atlas]}
            queries.append(updated_query)
    return queries


def generate_queries(parameters: dict, atlases: Optional[dict] = []):
    """
    Generate queries for the database.

    Parameters
    ----------
    parameters : dict
        The parameters to generate the queries.
    """
    queries: list[dict] = []
    for software, software_parameters in parameters.items():
        entity = software_parameters.get("entity")
        values = software_parameters.get("values")
        for value in values:
            query = {
                "query": {
                    "reconstruction_software": software,
                    entity: value,
                }
            }
            queries += [query]

    if atlases:
        queries = add_atlases_to_queries(queries, atlases)
    return queries


def add_session_and_subject_details(df: pd.DataFrame, procedure: Procedure):
    """
    Add the session and subject details to the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to add the details.
    procedure : Procedure
        The procedure to get the details.
    """
    session = procedure.session
    subject = session.subject
    # subject details
    df["subject_id"] = subject.subject_id
    df["subject_code"] = subject.subject_code
    df["sex"] = subject.sex
    df["height"] = subject.height
    df["weight"] = subject.weight
    df["handeness"] = subject.handedness
    # session details
    df["session_id"] = session.session_id
    df["timestamp"] = session.timestamp
    df["scan_tag"] = session.scan_tag
    df["study"] = session.study.name
    df["group"] = session.group.name
    df["condition"] = session.condition.name
    df["lab"] = session.lab.name
    df["age_at_scan"] = session.age_at_scan
    return df


def generate_destination_path(destination: str, query: dict):
    """
    Generate the destination path for the output files.

    Parameters
    ----------
    destination : str
        The path to store the output files.
    query : dict
        The query to generate the path.
    """
    path = Path(destination)
    for key, value in query.items():
        path = path / f"{key}-{value}".replace("reconstruction_", "")
    path.mkdir(parents=True, exist_ok=True)
    return path


def aggregate_tensor_results(procedures: QuerySet, destination: str, overwrite: bool):
    """
    Aggregate the results of the tensor estimations.

    Parameters
    ----------
    destination : str
        The path to store the output files.
    overwrite : bool
        Whether to overwrite existing files.
    """
    tensor_queries = generate_queries(TENSORS_PARAMETERS, atlases=AVAILABLE_ATLASES)
    for full_query in tqdm.tqdm(tensor_queries, desc="Aggregating tensor results"):
        query = full_query.get("query")
        print(query)
        query_destination = generate_destination_path(destination, query)
        data_destination = query_destination / "data.pkl"
        atlas_destination = query_destination / "atlas.pkl"
        if data_destination.exists() and atlas_destination.exists() and not overwrite:
            continue
        atlas = full_query.get("atlas")
        query_df = pd.DataFrame()
        for procedure in procedures:
            fname = procedure.get(query)
            if not fname or not Path(fname).exists():
                continue
            p_df = pd.read_pickle(fname)
            p_df = add_session_and_subject_details(p_df, procedure)
            query_df = pd.concat([query_df, p_df], ignore_index=True)
        if query_df.empty:
            continue
        query_df.to_pickle(data_destination)
        # save atlas to pickle file
        with open(atlas_destination, "wb") as f:
            pickle.dump(atlas, f)


def aggregate_qc_results(procedures: QuerySet, destination: str, overwrite: bool):
    """
    Aggregate the results of the quality control.

    Parameters
    ----------
    destination : str
        The path to store the output files.
    overwrite : bool
        Whether to overwrite existing files.
    """
    qc_queries = generate_queries(QC_PARAMETERS)
    for full_query in tqdm.tqdm(qc_queries, desc="Aggregating QC results"):
        query = full_query.get("query")
        query_destination = generate_destination_path(destination, query)
        data_destination = query_destination / "data.pkl"
        if data_destination.exists() and not overwrite:
            continue
        query_df = pd.DataFrame()
        for procedure in procedures:
            fname = procedure.get(query)
            if not fname:
                continue
            if fname.endswith(".csv"):
                p_df = pd.read_csv(fname, index_col=0)
            elif fname.endswith(".json"):
                p_df = pd.read_json(fname, orient="index").T
            p_df = add_session_and_subject_details(p_df, procedure)
            query_df = pd.concat([query_df, p_df], ignore_index=True)
        if query_df.empty:
            continue
        query_df.to_pickle(data_destination)


def aggregate_results(destination: str, overwrite: bool):
    """
    Aggregate the results of the procedures.

    Parameters
    ----------
    destination : str
        The path to store the output files.
    overwrite : bool
        Whether to overwrite existing files.
    """
    procedures = Procedure.objects.filter(name="kepost")
    aggregate_tensor_results(procedures, destination, overwrite)
    aggregate_qc_results(procedures, destination, overwrite)


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
        destination = kwargs.get("destination")
        overwrite = kwargs.get("overwrite")
        aggregate_results(destination, overwrite)
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
