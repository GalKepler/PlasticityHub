from kepost.atlases.available_atlases import AVAILABLE_ATLASES
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy import (
    TENSOR_PARAMETERS as DIPY_TENSOR_PARAMETERS,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3 import (
    TENSOR_PARAMETERS as MRTRIX3_TENSOR_PARAMETERS,
)

TENSORS_PARAMETERS = {
    "dipy": {"entity": "measure", "values": DIPY_TENSOR_PARAMETERS},
    "mrtrix3": {"entity": "measure", "values": MRTRIX3_TENSOR_PARAMETERS},
}
QC_PARAMETERS = {"qc": {"entity": "desc", "values": ["snr", "eddy"]}}
