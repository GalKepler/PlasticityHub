import pickle
import subprocess
import warnings
from pathlib import Path
from typing import Optional

import environ
import tqdm
from django.core.management.base import BaseCommand
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from plasticityhub.procedures.models import Procedure
from plasticityhub.utils.management.static.procedures.connectomes.connectomes import (
    init_connectome_wf,
)
from plasticityhub.utils.management.static.procedures.kepost.outputs import (
    AVAILABLE_ATLASES,
    CONNECTOME_PARAMETERS,
)

warnings.filterwarnings("ignore")

OUT_FNAME_TEMPLATE = "sub-{subject}_ses-{session}_rec-{rec}_atlas-{atlas}_desc-{desc}_scale-{scale}_meas-{stat_edge}"


def collect_atlases(atlases: dict):
    """
    Add the atlases to the queries.

    Parameters
    ----------
    base_queries : list[dict]
        The queries to add the atlases.
    atlases : dict
        The atlases to add to the queries.
    """
    atlases = {key: atlases[key] for key in atlases if "schaefer" not in key}
    queries = []
    atlases_copy = []
    for atlas in atlases:
        if "schaefer" in atlas:
            atlas_name = atlas.split("_")[0]
            density = atlas.split("_")[1]
            div = atlas.split("_")[2] + "networks"
            atlas_query = {"atlas": atlas_name, "den": density, "division": div}
        else:
            atlas_name = atlas
            atlas_query = {"atlas": atlas_name}
        atlas_query["subtype"] = "atlases"
        atlas_query["label"] = "WholeBrain"
        queries.append(atlas_query)
        atlases_copy.append({atlas: atlases[atlas]})
    return queries, atlases_copy


def generate_queries(parameters: dict):
    """
    Generate queries for the database.

    Parameters
    ----------
    parameters : dict
        The parameters to generate the queries.
    """
    queries: list[dict] = []
    for recon_algorithm, variations in parameters.items():
        entity = variations.get("entity")
        values = variations.get("values")
        for value in values:
            query = {
                "query": {
                    "reconstruction": recon_algorithm,
                    entity: value,
                }
            }
            queries += [query]
    return queries


def collect_session_and_subject_details(procedure: Procedure):
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
    return {
        "subject_id": subject.subject_id,
        "subject_code": subject.subject_code.replace("_", "")
        .replace(" ", "")
        .replace("\t", ""),
        "sex": subject.sex,
        "height": subject.height,
        "weight": subject.weight,
        "handeness": subject.handedness,
        # session details
        "session_id": session.session_id,
        "timestamp": session.timestamp,
        "scan_tag": session.scan_tag,
        "study": session.study.name,
        "group": session.group.name,
        "condition": session.condition.name,
        "lab": session.lab.name,
        "age_at_scan": session.age_at_scan,
    }


def generate_connectomes_destination_path(
    destination: str, demo: dict, tracts_query: dict, atlas_query: dict
):
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
    path = path if path.name == "connectomes" else path / "connectomes"
    for entity, key in zip(["subject", "session"], ["subject_code", "session_id"]):
        value = demo.get(key).replace("_", "")
        path = path / f"{entity}-{value}"
    for key, value in tracts_query.items():
        path = path / f"{key}-{value}".replace("reconstruction", "rec")
    for key in ["atlas", "den", "division"]:
        if key in atlas_query:
            value = atlas_query.get(key)
            path = path / f"{key}-{value}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_reconstruction_parameters(scales: list[str], stat_edges: list[str]):
    """
    Generate the reconstruction parameters for the connectomes.

    Parameters
    ----------
    scales : list[str]
        The scales to generate the connectomes.
    stat_edges : list[str]
        The statistical edges to generate the connectomes.
    """
    reconstruction_parameters = []
    for scale in scales:
        for stat_edge in stat_edges:
            for tck_weights_in in [True, False]:
                reconstruction_parameters.append(
                    {
                        "scale": scale,
                        "stat_edge": stat_edge,
                        "tck_weights_in": tck_weights_in,
                    }
                )
    return reconstruction_parameters


def generate_connectomes(
    destination: str,
    scales: list[str],
    stat_edges: list[str],
    nthreads: Optional[int] = 20,
    overwrite: bool = False,
):
    """
    Aggregate the connectome results.

    Parameters
    ----------
    destination : str
        The path to store the output files.
    reconstruction_parameters : list[dict], optional
        The reconstruction parameters to aggregate the results.
    overwrite : bool
        Whether to overwrite existing files.
    """
    print("Generating connectomes...")
    reconstruction_parameters = generate_reconstruction_parameters(scales, stat_edges)
    print(reconstruction_parameters)
    procedures = Procedure.objects.filter(name="kepost")
    tracts_queries = generate_queries(CONNECTOME_PARAMETERS)
    atlases_queries, atlases_copy = collect_atlases(AVAILABLE_ATLASES)
    for procedure in tqdm.tqdm(procedures, desc="Generating connectomes"):
        demo_dict = collect_session_and_subject_details(procedure)
        subject = (
            demo_dict.get("subject_code")
            .replace("_", "")
            .replace(" ", "")
            .replace("\t", "")
        )
        session = demo_dict.get("session_id")
        wf = Workflow(name=f"connectome_wf")
        # wf.base_dir = Path(destination) / "workflows"
        for tracts_query in tracts_queries:
            reconstruction_algorithm = tracts_query.get("query").get("reconstruction")
            tract_sift2_weight = {
                "reconstruction": reconstruction_algorithm,
                "desc": "SIFT2",
            }
            for atlas_query, atlas_copy in zip(atlases_queries, atlases_copy):
                tck = procedure.get(tracts_query.get("query"))
                parcellation = procedure.get(atlas_query)
                sift2_weights = procedure.get(tract_sift2_weight)
                if not tck or not parcellation or not sift2_weights:
                    continue
                query_destination = generate_connectomes_destination_path(
                    destination, demo_dict, tracts_query.get("query"), atlas_query
                )

                atlas_destination = query_destination / f"atlas.pkl"
                with open(atlas_destination, "wb") as f:
                    pickle.dump(atlas_copy, f)
                demo_destination = query_destination / f"demo.pkl"
                with open(demo_destination, "wb") as f:
                    pickle.dump(demo_dict, f)

                for combination in reconstruction_parameters:
                    scale = combination.get("scale")
                    stat_edge = combination.get("stat_edge")
                    tck_weights = combination.get("tck_weights_in")
                    desc = "SIFT2" if tck_weights else "unweighted"
                    out_fname = OUT_FNAME_TEMPLATE.format(
                        subject=subject,
                        session=session,
                        rec=reconstruction_algorithm,
                        atlas=atlas_query.get("atlas"),
                        scale=scale,
                        stat_edge=stat_edge,
                        desc=desc,
                    )
                    out_data = query_destination / f"{out_fname}_connectome.csv"
                    # out_assignments = query_destination / f"{out_fname}_assignments.txt"
                    if not overwrite and all(
                        [
                            out_data.exists(),
                            # out_assignments.exists(),
                            atlas_destination.exists(),
                            demo_destination.exists(),
                        ]
                    ):
                        continue
                    con_wf = init_connectome_wf(
                        reconstruction_algorithm=reconstruction_algorithm,
                        atlas_name=list(atlas_copy.keys())[0],
                        in_tracts=tck,
                        atlas_nifti=parcellation,
                        scale=scale,
                        stat_edge=stat_edge,
                        tck_weights=tck_weights,
                        sift2_weights=sift2_weights,
                        out_data=out_data,
                        # out_assignments=out_assignments,
                        nthreads=nthreads,
                    )
                    wf.add_nodes([con_wf])
        wf.run()
        # args = f"-nthreads 20 -quiet -symmetric -stat_edge {stat_edge} -out_assignments {out_assignments}"
        # if scale:
        #     args += f" -scale_{scale}"
        # if tck_weights:
        #     args += f" -tck_weights {sift2_weights}"
        # if overwrite:
        #     args += " -force"
        # cmd = f"tck2connectome {tck} {parcellation} {out_data} {args}"
        # subprocess.run(cmd, shell=True)


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
            "--scales",
            nargs="+",
            type=str,
            help="The scales to generate the connectomes.",
        )
        parser.add_argument(
            "--stat_edges",
            nargs="+",
            type=str,
            help="The statistical edges to generate the connectomes.",
        )
        parser.add_argument(
            "--nthreads",
            type=int,
            default=20,
            help="The number of threads to use.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Whether to overwrite existing files.",
        )

    def handle(self, *args, **kwargs):
        destination = kwargs.get("destination")
        scales = kwargs.get("scales")
        scales = [scale if scale != "None" else None for scale in scales]
        stat_edges = kwargs.get("stat_edges")
        nthreads = kwargs.get("nthreads")
        overwrite = kwargs.get("overwrite")
        generate_connectomes(
            destination=destination,
            scales=scales,
            stat_edges=stat_edges,
            overwrite=overwrite,
            nthreads=nthreads,
        )
        self.stdout.write(self.style.SUCCESS("Database updated successfully."))
