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
import re
import sys

import copier
import pytest
from typing import Dict
import subprocess

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
        "project_name": "Language Model",
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
    base["use_comet"] = "false"
    base["use_vscode"] = "false"

    return base


def _create_data_maximal(
    license: str, python_version: str, cuda_version: str
) -> Dict[str, str]:
    base = _create_data_base(license, python_version, cuda_version)

    base["use_pytorch"] = "true"
    base["use_tensorflow"] = "true"
    base["use_scikit_learn"] = "true"
    base["use_comet"] = "true"
    base["use_vscode"] = "true"

    return base


def _test_file_empty(text: str) -> None:
    assert len(text) == 0


def _test_file_starts_with_license_hashes(has_license: bool, text: str) -> None:
    if has_license:
        assert text.startswith("# Copyright ")
    else:
        assert not text.startswith("\n")
        assert not text.startswith("# Copyright")


def _test_file_starts_with_license_html(has_license: bool, text: str) -> None:
    if has_license:
        assert text.startswith("<!--\nCopyright ")
    else:
        assert not text.startswith("\n")
        assert not text.startswith("<!--\nCopyright ")


def _test_file_license_content(expected_license: str, text: str) -> None:
    actual_license: str

    if "Permission is hereby granted" in text:
        actual_license = "mit"
    elif "This file is part of" in text:
        actual_license = "lgpl30"
    else:
        actual_license = "none"

    assert expected_license == actual_license


def _test_file_two_newlines_after_license_hashes(has_license: bool, text: str) -> None:
    if has_license:
        newline_count = 0

        for line in text.splitlines():
            if line.startswith("#"):
                if newline_count > 0:
                    break
                else:
                    continue
            elif len(line) == 0:
                newline_count += 1
            else:
                break

        assert newline_count == 1


def _test_readme_licened(has_license: bool, text: str) -> None:
    if has_license:
        assert "-->\n\n# " in text


PYPROJECT_PATTERN_BAD_SPACING = re.compile(r"[,\[][ \t]*\n[ \t]*\n")


def _test_pyproject_toml(text: str) -> None:
    assert PYPROJECT_PATTERN_BAD_SPACING.search(text) is None


PYTHON_VERSION_WITH_DASH_PATTERN = re.compile(r"3-[0-9]+")


def _test_file_python_version_with_dot(text: str) -> None:
    assert PYTHON_VERSION_WITH_DASH_PATTERN.search(text) is None


def _test_file_formatting_black(path: str) -> None:
    result = subprocess.run(["black", "--check", path])

    assert result.returncode == 0


def _create_directory_test_minimal(license: str, cuda_version: str) -> DirectoryTest:
    result = DirectoryTest(
        child_files={
            ".copier-answers.yml": FileTest(),
            ".env.example.sh": FileTest(
                on_text=[
                    lambda text: _test_file_starts_with_license_hashes(
                        license != "none", text
                    ),
                    lambda text: _test_file_license_content(license, text),
                    lambda text: _test_file_two_newlines_after_license_hashes(
                        license != "none", text
                    ),
                    _test_file_python_version_with_dot,
                ]
            ),
            ".gitignore": FileTest(
                on_text=[
                    lambda text: _test_file_starts_with_license_hashes(
                        license != "none", text
                    ),
                    lambda text: _test_file_license_content(license, text),
                    lambda text: _test_file_two_newlines_after_license_hashes(
                        license != "none", text
                    ),
                    _test_file_python_version_with_dot,
                ]
            ),
            ".pdm-python": FileTest(),
            f"pdm.{sys.platform}.{('default' if cuda_version == 'not_applicable' else cuda_version)}.lock": FileTest(),
            "pdm.lock": FileTest(),
            "pyproject.toml": FileTest(
                on_text=[
                    lambda text: _test_file_starts_with_license_hashes(
                        license != "none", text
                    ),
                    lambda text: _test_file_license_content(license, text),
                    lambda text: _test_file_two_newlines_after_license_hashes(
                        license != "none", text
                    ),
                    _test_pyproject_toml,
                    _test_file_python_version_with_dot,
                ]
            ),
            "README.md": FileTest(
                on_text=[
                    lambda text: _test_file_starts_with_license_html(
                        license != "none", text
                    ),
                    lambda text: _test_file_license_content(license, text),
                    lambda text: _test_readme_licened(license != "none", text),
                    _test_file_python_version_with_dot,
                ]
            ),
        },
        child_directories={
            ".git": DirectoryTest(ignore_children=True),
            ".venv": DirectoryTest(ignore_children=True),
            "__pypackages__": DirectoryTest(ignore_children=True, optional=True),
            "language_model": DirectoryTest(
                child_files={
                    "__init__.py": FileTest(on_text=[_test_file_empty]),
                    "settings.py": FileTest(
                        on_text=[
                            lambda text: _test_file_starts_with_license_hashes(
                                license != "none", text
                            ),
                            lambda text: _test_file_license_content(license, text),
                            lambda text: _test_file_two_newlines_after_license_hashes(
                                license != "none", text
                            ),
                            _test_file_python_version_with_dot,
                        ],
                        on_path=[
                            _test_file_formatting_black,
                        ],
                    ),
                },
                child_directories={
                    "utils": DirectoryTest(
                        child_files={
                            "download_test.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ],
                                on_path=[
                                    _test_file_formatting_black,
                                ],
                            ),
                            "download.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ],
                                on_path=[
                                    _test_file_formatting_black,
                                ],
                            ),
                            "extract_test.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ],
                                on_path=[
                                    _test_file_formatting_black,
                                ],
                            ),
                            "extract.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ],
                                on_path=[
                                    _test_file_formatting_black,
                                ],
                            ),
                            "project_paths_test.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ]
                            ),
                            "project_paths.py": FileTest(
                                on_text=[
                                    lambda text: _test_file_starts_with_license_hashes(
                                        license != "none", text
                                    ),
                                    lambda text: _test_file_license_content(
                                        license, text
                                    ),
                                    lambda text: _test_file_two_newlines_after_license_hashes(
                                        license != "none", text
                                    ),
                                    _test_file_python_version_with_dot,
                                ],
                                on_path=[
                                    _test_file_formatting_black,
                                ],
                            ),
                            "__init__.py": FileTest(on_text=[_test_file_empty]),
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
                            "example_experiment.ipynb": FileTest(
                                on_text=[
                                    _test_file_python_version_with_dot,
                                ]
                            ),
                        }
                    ),
                    "tutorials": DirectoryTest(
                        child_files={
                            "example_tutorial.ipynb": FileTest(
                                on_text=[
                                    _test_file_python_version_with_dot,
                                ]
                            ),
                        }
                    ),
                }
            ),
            "scripts": DirectoryTest(
                child_files={
                    "pdm_lockfile.py": FileTest(
                        on_path=[
                            _test_file_formatting_black,
                        ]
                    ),
                }
            ),
        },
    )

    if license != "none":
        result.child_files["LICENSE.txt"] = FileTest()

    return result


def _create_directory_test_maximal(license: str, cuda_version: str) -> DirectoryTest:
    minimal = _create_directory_test_minimal(license, cuda_version)

    minimal.child_directories[".vscode"] = DirectoryTest(
        child_files={
            "settings.json": FileTest(),
            "extensions.json": FileTest(),
        }
    )

    minimal.child_directories["language_model"].child_directories["utils"].child_files[
        "comet.py"
    ] = FileTest()

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
        cleanup_on_error=False,
    )

    directory_test.run(copy_directory)

    result = subprocess.run(["pdm", "run", "lint:mypy"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint:pycodestyle"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint:pydocstyle"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint:bandit"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint:vulture"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint:isort", "--df"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "lint"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(
        ["pdm", "run", "format:black", "--diff"], cwd=copy_directory
    )

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "format:isort", "-c"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "format"], cwd=copy_directory)

    assert result.returncode == 0

    result = subprocess.run(["pdm", "run", "test"], cwd=copy_directory)

    assert result.returncode == 0


minimal_parameters = []
maximal_parameters = []

for license in ["mit", "lgpl30"]:
    minimal_parameters.append((license, "3-11"))

for python_version in ["3-8", "3-9", "3-10", "3-11"]:
    minimal_parameters.append(("none", python_version))


for python_version in ["3-8", "3-9", "3-10", "3-11"]:
    if sys.platform == "darwin":
        maximal_parameters.append((python_version, "default"))
    else:
        for cuda_version in ["default", "cuda-11-7", "cuda-11-8"]:
            maximal_parameters.append((python_version, cuda_version))


@pytest.mark.parametrize("license,python_version", minimal_parameters)
def test_minimal(license: str, python_version: str) -> None:
    """Test minimal Copier usage."""
    _run_copy_test(
        copy_name=f"minimal-{license}-{python_version}",
        data=_create_data_minimal(license=license, python_version=python_version),
        directory_test=_create_directory_test_minimal(license, "not_applicable"),
    )


@pytest.mark.parametrize("python_version,cuda_version", maximal_parameters)
def test_maximal(python_version: str, cuda_version: str) -> None:
    """Test maximal Copier usage."""
    _run_copy_test(
        copy_name=f"maximal-{python_version}-{cuda_version}",
        data=_create_data_maximal(
            license=license, python_version=python_version, cuda_version=cuda_version
        ),
        directory_test=_create_directory_test_maximal(license, cuda_version),
    )
