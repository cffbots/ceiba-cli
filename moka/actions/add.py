"""Module to add new jobs to the server.

API
---
.. autofunction:: add_jobs
"""

__all__ = ["add_jobs"]

import json
import logging
from collections import defaultdict
from typing import Any, DefaultDict

import numpy as np
import pandas as pd

from ..client import query_server
from ..client.mutations import create_job_mutation
from ..client.queries import create_properties_query
from ..utils import Options, json_properties_to_dataframe

logger = logging.getLogger(__name__)


def fetch_candidates(opts: Options) -> pd.DataFrame:
    """Retrieve candidates to compute from the server."""
    query = create_properties_query(opts.target_collection)
    reply = query_server(opts.url, query)
    return json_properties_to_dataframe(reply["properties"])


def create_mutations(row: pd.Series, opts: Options) -> str:
    """Create a list of mutations with the new jobs."""
    job_info = defaultdict(lambda: "null")  # type: DefaultDict[str, Any]
    prop_info = defaultdict(lambda: "null")  # type: DefaultDict[str, Any]
    job_info.update({
        "job_id": np.random.randint(0, 2147483647),
        "status": "AVAILABLE",
        "settings": format_settings(opts.settings)})

    prop_info.update({
        "smile_id": row._id,
        "smile": row.smile,
        "collection_name": generate_collection_name(opts.settings),
    })

    return create_job_mutation(job_info, prop_info)


def add_jobs(opts: Options) -> None:
    """Add new jobs to the server."""
    # Get the data to create the jobs
    df_candidates = fetch_candidates(opts)
    # Create the mutation to add the jobs in the server
    rows = df_candidates[["_id", "smile"]].iterrows()
    mutations = (create_mutations(row, opts)for _, row in rows)
    logger.info("New Jobs:")
    for query in mutations:
        reply = query_server(opts.url, query)
        logger.info(reply['createJob']['text'])


def format_settings(settings: Options) -> str:
    """Format the settings as string."""
    string = json.dumps(settings.to_dict())
    # Escape quotes
    return string.replace('\"', '\\"')


def generate_collection_name(settings: Options) -> str:
    """Create a name for the new collection based on the input provided by the user."""
    optimize = settings.optional.ligand.get("optimize", None)

    if optimize is None:
        return "rdkit/uff"

    job_type = optimize.job2
    if "ADF" in job_type.upper():
        return generate_adf_collection_name(optimize.s2)
    else:
        msg = f"{job_type} collection name generation has not been implemented!"
        raise NotImplementedError(msg)


def generate_adf_collection_name(optimize: Options) -> str:
    """Create collection name using the ADF optimization job."""
    job_settings = optimize.s2
    xc = job_settings.input.xc.copy()
    functional = '_'.join(xc.popitem())
    basisset = job_settings.input.basis.type
    core = basisset.job_settings.input.basis.core
    relativity = job_settings.input.get("relativity")
    if relativity is not None:
        if relativity.get("formalism") is None:
            relativity_name = "zora"
        else:
            relativity_name = relativity.formalism
    else:
        relativity_name = "none"

    name = f"{optimize.job2}/{functional}/{basisset}/core_{core}/relativity_{relativity_name}".lower()
    return name.replace(' ', '_')
