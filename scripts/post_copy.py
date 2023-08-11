# Copyright 2023 Sophie Katz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the “Software”), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
A script that is run after copier has finished copying files.

See
[this script's documentation in Notion](https://wooden-saturnalia-815.notion.site/Template-repository-structure-ac3d83fc57524b66bea29c8becb82eb6)
for more details.
"""


from typing import List
import argparse
import os
import shutil
import subprocess
import sys

from constants import PYTHON_VERSION_CHOICES, CUDA_VERSION_CHOICES


def create_argument_parser() -> argparse.ArgumentParser:
    """Define the command line arguments for this script.

    Can exit the script if the arguments are invalid.
    """
    parser = argparse.ArgumentParser(
        description="Post copy script for the ML copier template"
    )

    parser.add_argument(
        "--python-version",
        type=str,
        help="The Python version to use (example: 3-11)",
        choices=PYTHON_VERSION_CHOICES,
    )

    parser.add_argument(
        "--cuda-version",
        type=str,
        help="The CUDA version to use",
        choices=CUDA_VERSION_CHOICES,
    )

    return parser


def validate_arguments(argument_namespace: argparse.Namespace) -> None:
    """Validate the arguments passed to the script.

    Can exit the script if the arguments are invalid.
    """
    if argument_namespace.python_version is None:
        print("error: required argument --python-version missing")
        sys.exit(1)

    if argument_namespace.python_version not in PYTHON_VERSION_CHOICES:
        print(
            f"error: required argument --python-version must be one of: {PYTHON_VERSION_CHOICES}"
        )
        sys.exit(1)

    if argument_namespace.cuda_version is None:
        print("error: required argument --cuda-version missing")
        sys.exit(1)

    if argument_namespace.cuda_version not in CUDA_VERSION_CHOICES:
        print(
            f"error: required argument --cuda-version must be one of: {CUDA_VERSION_CHOICES}"
        )
        sys.exit(1)


def get_arguments() -> argparse.Namespace:
    """Gets the command line arguments for the script and validates them.

    Can exit the script if the arguments are invalid.
    """
    argument_parser = create_argument_parser()

    argument_namespace = argument_parser.parse_args()

    validate_arguments(argument_namespace)

    return argument_namespace


def is_copy_directory(copy_directory: str) -> bool:
    """Checks if the given directory is an output of copier for this template."""
    return os.path.exists(os.path.join(copy_directory, ".copier-answers.yml"))


def initialize_git_repository(copy_directory: str) -> None:
    """Initializes a git repository in the given directory.

    Can exit the script if it fails."""
    result = subprocess.run(["git", "init", "."], cwd=copy_directory)

    if result.returncode == 1:
        sys.exit(1)


def venv_exists(copy_directory: str) -> bool:
    """Checks if the given directory has a venv created."""
    return os.path.exists(os.path.join(copy_directory, ".venv"))


def create_venv(pdm_path: str, copy_directory: str, python_version: str) -> None:
    """Creates a venv for the given directory.

    Can exit the script if it fails.
    """
    print(f"info: creating venv for python {python_version}...")

    result = subprocess.run(
        [pdm_path, "venv", "create", "-f", python_version], cwd=copy_directory
    )

    if result.returncode == 0:
        print("info: venv successfully created")
    else:
        print(f"error: unable to create venv (exit status: {result.returncode})")
        sys.exit(1)


def get_pdm_install_arguments(pdm_path: str, cuda_version: str) -> List[str]:
    """Gets the arguments to the PDM install command."""
    return [
        pdm_path,
        "install",
        "-G",
        cuda_version,
        "-L",
        f"pdm.{sys.platform}.{cuda_version}.lock",
        "--skip=:pre",
    ]


def pdm_install(pdm_path: str, cuda_version: str) -> None:
    """Installs dependencies with PDM.

    This bootstraps multiple PDM lockfile management. Can exit the script if it fails.
    """
    print("info: installing dependencies from pyproject.toml with pdm...")

    result = subprocess.run(
        get_pdm_install_arguments(pdm_path, cuda_version),
        env={"PDM_IGNORE_ACTIVE_VENV": "true"},
        cwd=copy_directory,
    )

    if result.returncode == 0:
        print("info: dependencies successfully installed")
    else:
        print(
            f"error: unable to install dependencies (exit status: {result.returncode})"
        )
        sys.exit(1)


def use_pdm_lock(pdm_path: str, copy_directory: str, cuda_version: str) -> None:
    """Uses the PDM lock file that was just installed.

    Can exit the script if it fails.
    """
    print(f"info: using pdm lock file for {cuda_version}...")

    result = subprocess.run(
        [
            pdm_path,
            "run",
            "lockfile",
            "use",
            "default" if cuda_version == "not_applicable" else cuda_version,
        ],
        cwd=copy_directory,
    )

    if result.returncode == 0:
        print("info: pdm lock file successfully used")
    else:
        print(f"error: unable to use pdm lock file (exit status: {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    # Get the arguments for this script and validate them.
    arguments = get_arguments()

    # Detect PDM
    pdm_path = shutil.which("pdm")

    if pdm_path is None:
        print("error: pdm must be installed and on the PATH")
        sys.exit(1)

    print(f"info: using pdm at {pdm_path}")

    # Set the copy directory to CWD.
    copy_directory = os.getcwd()

    # Verify that the copy directory is actually the output of this template.
    if not is_copy_directory(copy_directory):
        print(f"error: {copy_directory} must be the output of copier for this template")
        print()
        print("note: it does not appear to be because .copier-answers.yml is missing")

    # Initialize a git repository in the copy directory.
    initialize_git_repository(copy_directory)

    # Initialize a venv if it doesn't already exist.
    if venv_exists(copy_directory):
        print(f"info: {copy_directory} already has a venv")
    else:
        create_venv(
            pdm_path, copy_directory, str(arguments.python_version).replace("-", ".")
        )

    # Install dependencies with PDM.
    pdm_install(pdm_path, arguments.cuda_version)

    # Use the newly created PDM lock.
    use_pdm_lock(pdm_path, copy_directory, arguments.cuda_version)

    # Print a warning about packages that may not be useful.
    print()
    print(
        "warning: Some packages are installed that may not be immediately useful for this project. Please look at pyproject.toml and remove any that you will not use."
    )
