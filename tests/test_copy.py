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

"""Integration test for running Copier with different parameterizations.

Then tests rendered files against expected results.
"""


import os

import copier
import pytest
from typing import Dict

from tests.testing_utils import (
    COPIES_DIRECTORY,
    DirectoryTest,
    FileTest,
    before_integration_test,
)


def _create_data_base(
    license: str, python_version: str, cuda_version: str
) -> Dict[str, str]:
    return {
        "project_name": "test_project",
        "project_description": "A toy language model using transformers.",
        "module_name": "language_model",
        "package_name": "language-model",
        "package_version": "0.1.0",
        "author_name": "Sophie Katz",
        "author_email": "sophie@example.com",
        "license": license,
        "copyright_holder": "Sophie Katz",
        "python_version": python_version,
        "cuda_version": cuda_version,
    }


def _create_data_minimal(license: str, python_version: str) -> Dict[str, str]:
    base = _create_data_base(license, python_version, "not_applicable")

    base["use_pytorch"] = "false"
    base["use_tensorflow"] = "false"
    base["use_scikit_learn"] = "false"
    base["use_comet_ai"] = "false"
    base["use_vscode"] = "false"

    return base


def _create_data_maximal(
    license: str, python_version: str, cuda_version: str
) -> Dict[str, str]:
    base = _create_data_base(license, python_version, cuda_version)

    base["use_pytorch"] = "true"
    base["use_tensorflow"] = "true"
    base["use_scikit_learn"] = "true"
    base["use_comet_ai"] = "true"
    base["use_vscode"] = "true"

    return base


def _create_directory_test_minimal(has_license: bool) -> DirectoryTest:
    result = DirectoryTest(
        child_files={
            ".copier-answers.yml": FileTest(),
            ".env.example.sh": FileTest(),
            ".gitignore": FileTest(),
            ".pdm-python": FileTest(),
            "pdm.lock": FileTest(),
            "pyproject.toml": FileTest(),
            "README.md": FileTest(),
        },
        child_directories={
            ".venv": DirectoryTest(ignore_children=True),
            "language_model": DirectoryTest(
                child_files={
                    "__init__.py": FileTest(),
                    "settings.py": FileTest(),
                },
                child_directories={
                    "utils": DirectoryTest(
                        child_files={
                            "download_test.py": FileTest(),
                            "download.py": FileTest(),
                            "extract_test.py": FileTest(),
                            "extract.py": FileTest(),
                            "project_paths_test.py": FileTest(),
                            "project_paths.py": FileTest(),
                            "__init__.py": FileTest(),
                        }
                    )
                },
            ),
            "language_model.egg-info": DirectoryTest(
                ignore_children=True, optional=True
            ),
            "notebooks": DirectoryTest(
                child_directories={
                    "experiments": DirectoryTest(
                        child_files={
                            "example_experiment.ipynb": FileTest(),
                        }
                    ),
                    "tutorials": DirectoryTest(
                        child_files={
                            "example_tutorial.ipynb": FileTest(),
                        }
                    ),
                }
            ),
            "scripts": DirectoryTest(
                child_files={
                    "check_pdm_lock.py": FileTest(),
                    "use_pdm_lock.py": FileTest(),
                }
            ),
        },
    )

    if has_license:
        result.child_files["LICENSE.txt"] = FileTest()

    return result


def _create_directory_test_maximal(
    has_license: bool, cuda_version: str
) -> DirectoryTest:
    minimal = _create_directory_test_minimal(has_license)

    minimal.child_directories[".vscode"] = DirectoryTest(
        child_files={
            "settings.json": FileTest(),
            "extensions.json": FileTest(),
        }
    )

    minimal.child_directories["language_model"].child_directories["utils"].child_files[
        "comet.py"
    ] = FileTest()

    minimal.child_files[f"pdm.{cuda_version}.lock"] = FileTest()

    return minimal


def _run_copy_test(
    copy_name: str, data: Dict[str, str], directory_test: DirectoryTest
) -> None:
    before_integration_test(copy_name)

    copy_directory = os.path.join(COPIES_DIRECTORY, copy_name)

    copier.run_copy(
        ".",
        copy_directory,
        data=data,
        unsafe=True,
    )

    directory_test.run(copy_directory)


minimal_parameters = []
maximal_parameters = []

for license in ["none", "mit", "lgpl30"]:
    minimal_parameters.append((license, "3.11"))

for python_version in ["3.8", "3.9", "3.10", "3.11"]:
    minimal_parameters.append(("none", python_version))


for python_version in ["3.8", "3.9", "3.10", "3.11"]:
    for cuda_version in ["cpu", "cuda-11-7", "cuda-11-8"]:
        maximal_parameters.append((python_version, cuda_version))


@pytest.mark.parametrize("license,python_version", minimal_parameters)
def test_minimal(license: str, python_version: str) -> None:
    """Test minimal Copier usage."""
    _run_copy_test(
        copy_name=f"minimal-{license}-{python_version}",
        data=_create_data_minimal(license=license, python_version=python_version),
        directory_test=_create_directory_test_minimal(license != "none"),
    )


@pytest.mark.parametrize("python_version,cuda_version", maximal_parameters)
def test_maximal(python_version: str, cuda_version: str) -> None:
    """Test maximal Copier usage."""
    _run_copy_test(
        copy_name=f"maximal-{license}-{python_version}-{cuda_version}",
        data=_create_data_maximal(
            license=license, python_version=python_version, cuda_version=cuda_version
        ),
        directory_test=_create_directory_test_maximal(license != "none", cuda_version),
    )
