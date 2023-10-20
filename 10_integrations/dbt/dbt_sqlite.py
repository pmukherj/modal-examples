# ---
# cmd: ["modal", "run", "10_integrations/dbt/dbt_sqlite.py::run"]
# ---
#
# This is a simple demonstration of how to run a dbt-core project on Modal
# using the dbt-sqlite adapter.
#
# The underlying DBT data and models are from https://docs.getdbt.com/docs/get-started/getting-started-dbt-core
# To run this example, first run the meltano example in `10_integrations/meltano/` to load the required data
# into sqlite.
#
# **Run this example:**
#
# ```
# modal run dbt_sqlite.py::stub.run
# ```
#
# **Launch an interactive sqlite3 shell on the output database:**
#
# ```
# modal run dbt_sqlite.py::stub.explore
# ```


import os
import subprocess
import sys
import typing
from pathlib import Path

import modal

LOCAL_DBT_PROJECT = Path(__file__).parent / "sample_proj_sqlite"
REMOTE_DBT_PROJECT = "/sample_proj"
RAW_SCHEMAS = "/raw"
OUTPUT_SCHEMAS = "/db"

# Create an environment dict that will be usable by dbt templates:
dbt_env = modal.Secret.from_dict(
    {
        "RAW_DB_PATH": f"{RAW_SCHEMAS}/jaffle_shop_raw.db",
        "OUTPUT_SCHEMAS_PATH": OUTPUT_SCHEMAS,
        "MAIN_DB_PATH": f"{OUTPUT_SCHEMAS}/main.db",
    }
)

image = (
    modal.Image.debian_slim()
    .pip_install("dbt-core~=1.3.0", "dbt-sqlite~=1.3.0")
    .run_commands("apt-get install -y git")
)

# raw data loaded by meltano, see the meltano example in 10_integrations/meltano
raw_volume = modal.NetworkFileSystem.from_name("meltano_volume")

# output schemas
db_volume = modal.NetworkFileSystem.persisted("dbt_dbs")
project_mount = modal.Mount.from_local_dir(
    LOCAL_DBT_PROJECT, remote_path=REMOTE_DBT_PROJECT
)
stub = modal.Stub(image=image, mounts=[project_mount], secrets=[dbt_env])


@stub.function(
    network_file_systems={RAW_SCHEMAS: raw_volume, OUTPUT_SCHEMAS: db_volume}
)
def dbt_cli(subcommand: typing.List):
    os.chdir(REMOTE_DBT_PROJECT)
    cmd = ["dbt"] + subcommand
    print(f"Running {' '.join(cmd)} against {REMOTE_DBT_PROJECT}")
    subprocess.check_call(cmd)


@stub.local_entrypoint()
def run():
    dbt_cli.remote(["run"])


@stub.local_entrypoint()
def debug():
    dbt_cli.remote(["debug"])


@stub.function(
    interactive=sys.stdout.isatty(),
    network_file_systems={RAW_SCHEMAS: raw_volume, OUTPUT_SCHEMAS: db_volume},
    timeout=86400,
    image=modal.Image.debian_slim().apt_install("sqlite3"),
)
def explore():
    # explore the output database interactively using the sqlite3 shell
    os.execlp("sqlite3", "sqlite3", os.environ["MAIN_DB_PATH"])
