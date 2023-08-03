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

import dataclasses
import os
import shutil
import io
from typing import Callable, Optional

COPIES_DIRECTORY = os.path.join(os.getcwd(), "copies")


def before_integration_test() -> None:
    """Code to be run before all integration tests."""
    if not os.path.exists(".git") or not os.path.exists("copier.yml"):
        raise Exception(
            "this script must be run from the root directory of the copier-ml repository"
        )

    shutil.rmtree(COPIES_DIRECTORY, ignore_errors=True)
    os.mkdir(COPIES_DIRECTORY)


@dataclasses.dataclass
class FileTest:
    optional: bool = False
    on_read_binary: Optional[Callable[[io.BufferedReader], None]] = None
    on_read_text: Optional[Callable[[io.TextIOWrapper], None]] = None

    def run(self, path: str) -> None:
        if not self.optional:
            assert os.path.isfile(
                path
            ), f"path is expected to exist and be a file: {path!r}"

        if os.path.isfile(path):
            if self.on_read_binary is not None and self.on_read_text is not None:
                raise Exception(
                    "FileTest cannot have both on_read_binary and on_read_text set"
                )
            elif self.on_read_binary is not None:
                with open(path, mode="rb") as file:
                    self.on_read_binary(file)
            elif self.on_read_text is not None:
                with open(path, encoding="utf-8") as file:
                    self.on_read_text(file)


@dataclasses.dataclass
class DirectoryTest:
    optional: bool = False
    child_files: dict[str, FileTest] = dataclasses.field(default_factory=dict)
    child_directories: dict[str, "DirectoryTest"] = dataclasses.field(
        default_factory=dict
    )
    ignore_children: bool = False

    def run(self, path: str) -> None:
        if not self.optional:
            assert os.path.isdir(
                path
            ), f"path is expected to exist and be a directory: {path!r}"

        if self.ignore_children:
            if len(self.child_files) > 0:
                raise Exception(
                    "child_files cannot be set when ignore_children is True"
                )

            if len(self.child_directories) > 0:
                raise Exception(
                    "child_directories cannot be set when ignore_children is True"
                )
        elif os.path.isdir(path):
            for child_directory_name, child_directory in self.child_directories.items():
                child_directory.run(os.path.join(path, child_directory_name))

            for child_file_name, child_file in self.child_files.items():
                child_file.run(os.path.join(path, child_file_name))

            for child_name in os.listdir(path):
                assert (
                    child_name in self.child_files
                    or child_name in self.child_directories
                ), f"unexpected child in directory {path!r}: {child_name!r}"
