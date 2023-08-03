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
import subprocess
import sys

PYTHON_VERSION_PATTERN = re.compile(r"^3\.\d+$")

CUDA_VERSION_CHOICES = ["not_applicable", "cpu", "cuda-11-7", "cuda-11-8"]


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Post copy script for the ML copier template", exit_on_error=False
    )

    parser.add_argument(
        "--python-version",
        type=str,
        help="The Python version to use (example: 3.11)",
    )

    parser.add_argument(
        "--cuda-version",
        type=str,
        help="The CUDA version to use (not_applicable means that no dependencies use CUDA)",
        choices=["not_applicable", "cpu", "cuda-11-7", "cuda-11-8"],
    )

    return parser


def get_arguments() -> argparse.Namespace:
    argument_parser = create_argument_parser()

    try:
        argument_namespace = argument_parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"error: {e}")
        sys.exit(1)

    if argument_namespace.python_version is None:
        print("error: required argument --python-version missing")
        sys.exit(1)

    if PYTHON_VERSION_PATTERN.match(str(argument_namespace.python_version)) is None:
        print(f"error: --python-version must match {PYTHON_VERSION_PATTERN.pattern}")
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


def create_venv(copy_directory: str, python_version: str) -> None:
    print(f"info: creating venv for python {python_version}...")

    result = subprocess.run(["pdm", "venv", "create", "-f", python_version])

    if result.returncode == 0:
        print("info: venv successfully created")
    else:
        print(f"error: unable to create venv (exit status: {result.returncode})")
        sys.exit(1)


def has_pdm_lock(cuda_version: str) -> bool:
    return cuda_version != "not_applicable"


def get_pdm_install_arguments(cuda_version: str) -> list[str]:
    if has_pdm_lock(cuda_version):
        return [
            "pdm",
            "install",
            "-G",
            cuda_version,
            "-L",
            f"pdm.{cuda_version}.lock",
            "--skip=:pre",
        ]
    else:
        return ["pdm", "install"]


def pdm_install(cuda_version: str) -> None:
    print(f"info: installing dependencies from pyproject.toml with pdm...")

    result = subprocess.run(get_pdm_install_arguments(cuda_version))

    if result.returncode == 0:
        print("info: dependencies successfully installed")
    else:
        print(
            f"error: unable to install dependencies (exit status: {result.returncode})"
        )
        sys.exit(1)


def use_pdm_lock(cuda_version: str) -> None:
    print(f"info: using pdm lock file for {cuda_version}...")

    result = subprocess.run(["python3", "scripts/use_pdm_lock.py", cuda_version])

    if result.returncode == 0:
        print("info: pdm lock file successfully used")
    else:
        print(f"error: unable to use pdm lock file (exit status: {result.returncode})")
        sys.exit(1)


def check_pdm_lock() -> None:
    print(f"info: checking pdm lock file...")

    result = subprocess.run(["python3", "scripts/check_pdm_lock.py"])

    if result.returncode == 0:
        print("info: pdm lock file is valid")
    else:
        print(f"error: pdm lock file is invalid (exit status: {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    arguments = get_arguments()

    copy_directory = os.getcwd()

    if not is_copy_directory(copy_directory):
        print(f"error: {copy_directory} must be the output of copier for this template")
        print()
        print("note: it does not appear to be because .copier-answers.yml is missing")

    if venv_exists(copy_directory):
        print(f"info: {copy_directory} already has a venv")
    else:
        create_venv(copy_directory, arguments.python_version)

    pdm_install(arguments.cuda_version)

    if has_pdm_lock(arguments.cuda_version):
        use_pdm_lock(arguments.cuda_version)
        check_pdm_lock()

    print()
    print(
        "warning: Some packages are installed that may not be immediately useful for this project. Please look at pyproject.toml and remove any that you will not use."
    )
