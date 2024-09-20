from kepost.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def init_connectome_wf(
    reconstruction_algorithm: str,
    atlas_name: str,
    in_tracts: str,
    atlas_nifti: str,
    scale: str,
    stat_edge: str,
    tck_weights: bool,
    sift2_weights: str,
    out_data: str,
    out_assignments: str,
    nthreads: int = 1,
    # name: str = "connectome_wf",
) -> Workflow:
    """
    Workflow to generate connectomes using MRtrix3.
    Parameters
    ----------
    name : str
        Name of the workflow.
    Returns
    -------
    workflow : Workflow
        Workflow object.
    """
    desc = "SIFT2" if tck_weights else "unweighted"
    workflow = Workflow(
        name=f"connectome_parc-{atlas_name}_scale-{scale}_metric-{stat_edge}_weights-{desc}_in-tracts-{reconstruction_algorithm}"
    )
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "in_tracts",
                "atlas_nifti",
                "scale",
                "stat_edge",
                "sift2_weights",
                "out_data",
                "out_assignments",
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.atlas_nifti = atlas_nifti
    inputnode.inputs.in_tracts = in_tracts
    inputnode.inputs.scale = scale
    inputnode.inputs.stat_edge = stat_edge
    inputnode.inputs.sift2_weights = sift2_weights
    inputnode.inputs.out_data = out_data
    inputnode.inputs.out_assignments = out_assignments

    connectome = pe.Node(
        mrt.BuildConnectome(nthreads=nthreads, args="-quiet"),
        name="connectome",
    )
    if scale is not None:
        connectome.inputs.scale = scale
    workflow.connect(
        [
            (
                inputnode,
                connectome,
                [
                    ("in_tracts", "in_tracts"),
                    ("atlas_nifti", "in_nodes"),
                    ("stat_edge", "stat_edge"),
                    ("out_data", "out_connectome"),
                    ("out_assignments", "out_assignments"),
                ],
            ),
        ]
    )
    if tck_weights:  # type: ignore[operator]
        workflow.connect(
            [
                (
                    inputnode,
                    connectome,
                    [
                        ("sift2_weights", "tck_weights_in"),
                    ],
                ),
            ]
        )
    return workflow
