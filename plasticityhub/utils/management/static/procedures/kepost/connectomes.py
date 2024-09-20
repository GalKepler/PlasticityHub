"""
Utility functions for the connectome module.
"""

SCALES = ["length", "invlength", "invnodevol", None]
STATS = ["sum", "mean", "min", "max"]
TCK_WEIGHTS = [False, True]
COMBINATIONS = [
    {"scale": scale, "stat_edge": metric, "tck_weights_in": tck_weights}
    for scale in SCALES
    for metric in STATS
    for tck_weights in TCK_WEIGHTS
]
