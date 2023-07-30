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
from copier_ml.testing_utils import (
    before_integration_test,
    COPIES_DIRECTORY,
    FileTest,
    DirectoryTest,
)


def _run_copy_test(name: str, directory_test: DirectoryTest) -> None:
    before_integration_test()

    copier.run_copy(
        ".",
        os.path.join(COPIES_DIRECTORY, name),
        data={
            "project_name": "test_project",
        },
    )

    directory_test.run(os.path.join(COPIES_DIRECTORY, name))


def test_minimal() -> None:
    """Test minimal Copier usage."""
    _run_copy_test(
        name="minimal",
        directory_test=DirectoryTest(
            child_files={
                ".copier-answers.yml": FileTest(),
            },
            child_directories={
                ".vscode": DirectoryTest(
                    child_files={
                        "extensions.json": FileTest(),
                        "settings.json": FileTest(),
                    }
                ),
                "test_project": DirectoryTest(
                    child_files={
                        "__init__.py": FileTest(),
                    }
                ),
            },
        ),
    )
