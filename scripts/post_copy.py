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

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import List, Dict

PYTHON_VERSION_CHOICES = ["3-8", "3-9", "3-10", "3-11"]
CUDA_VERSION_CHOICES = ["not_applicable", "default", "cuda-11-7", "cuda-11-8"]


def create_argument_parser() -> argparse.ArgumentParser:
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
        help="The CUDA version to use (not_applicable means that no dependencies use CUDA)",
        choices=CUDA_VERSION_CHOICES,
    )

    return parser


def get_arguments() -> argparse.Namespace:
    argument_parser = create_argument_parser()

    argument_namespace = argument_parser.parse_args()

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

    return argument_namespace


def is_copy_directory(copy_directory: str) -> bool:
    return os.path.exists(os.path.join(copy_directory, ".copier-answers.yml"))


def venv_exists(copy_directory: str) -> bool:
    return os.path.exists(os.path.join(copy_directory, ".venv"))


def create_venv(pdm_path: str, copy_directory: str, python_version: str) -> None:
    print(f"info: creating venv for python {python_version}...")

    result = subprocess.run([pdm_path, "venv", "create", "-f", python_version])

    if result.returncode == 0:
        print("info: venv successfully created")
    else:
        print(f"error: unable to create venv (exit status: {result.returncode})")
        sys.exit(1)


def get_pdm_install_arguments(pdm_path: str, cuda_version: str) -> List[str]:
    if cuda_version == "not_applicable":
        return [
            pdm_path,
            "install",
            "-L",
            f"pdm.{sys.platform}.default.lock",
            "--skip=:pre",
        ]
    else:
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
    print(f"info: installing dependencies from pyproject.toml with pdm...")

    result = subprocess.run(
        get_pdm_install_arguments(pdm_path, cuda_version),
        env={"PDM_IGNORE_ACTIVE_VENV": "true"},
    )

    if result.returncode == 0:
        print("info: dependencies successfully installed")
    else:
        print(
            f"error: unable to install dependencies (exit status: {result.returncode})"
        )
        sys.exit(1)


def use_pdm_lock(pdm_path: str, cuda_version: str) -> None:
    print(f"info: using pdm lock file for {cuda_version}...")

    result = subprocess.run([pdm_path, "run", "lockfile", "use", "default" if cuda_version == "not_applicable" else cuda_version])

    if result.returncode == 0:
        print("info: pdm lock file successfully used")
    else:
        print(f"error: unable to use pdm lock file (exit status: {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    arguments = get_arguments()

    copy_directory = os.getcwd()

    result = subprocess.run(["git", "init", "."])

    if result.returncode == 1:
        sys.exit(1)

    if not is_copy_directory(copy_directory):
        print(f"error: {copy_directory} must be the output of copier for this template")
        print()
        print("note: it does not appear to be because .copier-answers.yml is missing")

    pdm_path = shutil.which("pdm")

    if pdm_path is None:
        print("error: pdm must be installed and on the PATH")
        sys.exit(1)

    print(f"info: using pdm at {pdm_path}")

    if venv_exists(copy_directory):
        print(f"info: {copy_directory} already has a venv")
    else:
        create_venv(
            pdm_path, copy_directory, str(arguments.python_version).replace("-", ".")
        )

    pdm_install(pdm_path, arguments.cuda_version)

    # if has_pdm_lock(arguments.cuda_version):
    use_pdm_lock(pdm_path, arguments.cuda_version)
    #     check_pdm_lock()

    print()
    print(
        "warning: Some packages are installed that may not be immediately useful for this project. Please look at pyproject.toml and remove any that you will not use."
    )
