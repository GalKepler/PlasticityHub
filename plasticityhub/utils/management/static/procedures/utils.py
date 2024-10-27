from importlib.resources import files
from json import loads
from pathlib import Path
from typing import Union

from bids.layout import Config, parse_file_entities


def resource_filename(package, resource):
    return str(files(package).joinpath(resource))


_kepost_pybids_spec = loads(
    Path(resource_filename("kepost", "interfaces/bids/static/kepost.json")).read_text()
)

KEPOST_CONFIG = Config(**_kepost_pybids_spec)
BIDS_CONFIG = Config.load("bids")
DERIVATIVES_CONFIG = Config.load("derivatives")


def parse_output(
    in_file: Union[str, Path],
    configs: list = [BIDS_CONFIG, DERIVATIVES_CONFIG, KEPOST_CONFIG],
) -> dict:
    """
    Parse the output file to extract BIDS entities.

    Parameters
    ----------
    in_file : Union[str, Path]
        The path to the output file.
    configs : list
        The BIDS configuration files to use for parsing the
        output file. Default is [BIDS_CONFIG, DERIVATIVES_CONFIG, KEPOST_CONFIG].

    Returns
    -------
    dict
        The BIDS entities extracted from the output file
    """
    entities = {}
    for config in configs:
        cur_entities = parse_file_entities(in_file, config=config)
        entities.update(cur_entities)
    return entities


def parse_session(
    output_directory: Union[str, Path],
    configs: list = [BIDS_CONFIG, DERIVATIVES_CONFIG, KEPOST_CONFIG],
) -> dict:
    """
    Parse the output directory to extract BIDS entities.

    Parameters
    ----------
    output_directory : Union[str, Path]
        The path to the output directory.
    configs : list
        The BIDS configuration files to use for parsing the
        output file. Default is [BIDS_CONFIG, DERIVATIVES_CONFIG, KEPOST_CONFIG].

    Returns
    -------
    dict
        The BIDS entities extracted from the output directory
    """
    result = {}
    for in_file in Path(output_directory).rglob("*"):
        if in_file.is_file():
            entities = parse_output(in_file, configs)
            result[str(in_file)] = entities
    return result
