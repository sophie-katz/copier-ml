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


"""Command-line utility for managing PDM lockfiles."""


import argparse
import os
import re
import subprocess
import sys
from typing import List, Tuple

from colored import Fore, Style


PDM_LOCKFILE_PATTERN = re.compile(r"pdm\.([^.]+)\.([^.]+)\.lock")
CURRENT_PDM_LOCKFILE = "pdm.lock"


def print_info(*args) -> None:
    print(f"{Fore.green}==> info:{Style.reset}", *args)


def print_note(*args) -> None:
    print(f"{Fore.grey_69}  > note:{Style.reset}", *args)


def print_fix(*args) -> None:
    print(f"{Fore.magenta}  > fix:{Style.reset}", *args)


def print_error(*args) -> None:
    print(f"{Fore.red}==> error:{Style.reset}", *args)


def print_command_running(*args) -> None:
    print(f"{Fore.orange_1}  > running: {list(args)}{Style.reset}")


def print_command_exit_status(exit_status: int) -> None:
    if exit_status == 0:
        print(f"{Fore.green}  > exit status: 0{Style.reset}")
    else:
        print(f"{Fore.red}  > exit status: {exit_status}{Style.reset}")


def run_command(*args) -> bool:
    print_command_running(*args)

    result = subprocess.run(args)

    print_command_exit_status(result.returncode)

    return result.returncode == 0


def ensure_pdm_lockfile_valid() -> None:
    if os.path.exists(CURRENT_PDM_LOCKFILE) and not os.path.islink(
        CURRENT_PDM_LOCKFILE
    ):
        print_error(f"'{CURRENT_PDM_LOCKFILE}' must be a symbolic link")
        print()
        print_note(
            f"this is most likely because '{CURRENT_PDM_LOCKFILE}' was created by PDM without using lockfile management"
        )
        print()
        print_fix(f"delete it or move '{CURRENT_PDM_LOCKFILE}' and then try again")
        sys.exit(1)


def get_pdm_lockfile_name(group_name: str) -> str:
    return f"pdm.{sys.platform}.{group_name}.lock"


def use_pdm_lockfile(group_name: str) -> None:
    if os.path.exists(CURRENT_PDM_LOCKFILE):
        os.remove(CURRENT_PDM_LOCKFILE)

    os.symlink(get_pdm_lockfile_name(group_name), CURRENT_PDM_LOCKFILE)

    print_info(f"lockfile set to group {group_name}")


def list_pdm_lockfiles() -> List[Tuple[bool, str, str]]:
    results = []

    for filename in os.listdir():
        match = PDM_LOCKFILE_PATTERN.match(filename)
        if match:
            is_current = (
                os.path.exists(CURRENT_PDM_LOCKFILE)
                and os.path.basename(os.readlink(CURRENT_PDM_LOCKFILE)) == filename
            )
            results.append((is_current, match.group(1), match.group(2)))

    return results


def command_check(arguments: argparse.Namespace) -> None:
    if not os.path.exists(CURRENT_PDM_LOCKFILE):
        print_error(f"no lockfile set")
        print()
        print_note(f"file '{CURRENT_PDM_LOCKFILE}' does not exist in {os.getcwd()}")
        print()
        print_fix(f"run this command to list available lockfiles:")
        print_fix(f"  $ pdm run lockfile list")
        print_fix()
        print_fix(f"then run this command to use on of those lockfiles:")
        print_fix(f"  $ pdm run lockfile use <GROUP>")
        print_fix()
        print_fix(f"if there is no lockfile available that applies, run:")
        print_fix(f"  $ pdm run lockfile add <GROUP>")
        sys.exit(1)

    if not os.path.islink(CURRENT_PDM_LOCKFILE):
        print_error(f"'{CURRENT_PDM_LOCKFILE}' must be a symbolic link")
        sys.exit(1)

    print_info(f"'{CURRENT_PDM_LOCKFILE}' is set up correctly")


def command_list(arguments: argparse.Namespace) -> None:
    pdm_lockfiles = list_pdm_lockfiles()

    if len(pdm_lockfiles) > 0:
        print_info("available lockfiles:")

        for is_current, platform, group_name in pdm_lockfiles:
            print(f"  {('*' if is_current else '')}{group_name} (platform: {platform})")
    else:
        print_info("no available lockfiles")
        print()
        print_fix(f"run this command to add a new one:")
        print_fix(f"  $ pdm run lockfile add <GROUP>")
        sys.exit(1)


def command_use(arguments: argparse.Namespace) -> None:
    pdm_lockfiles = list_pdm_lockfiles()

    found = False
    found_group = False

    for _, platform, group_name in pdm_lockfiles:
        if group_name == arguments.group_name:
            found_group = True

            if platform == sys.platform:
                found = True
                break

    if not found and found_group:
        print_error("group does not have a lockfile for this platform")
        print()
        print_fix(f"run this command to list available groups:")
        print_fix(f"  $ pdm run lockfile list")
        print_fix()
        print_fix(f"or run this command to add one:")
        print_fix(f"  $ pdm run lockfile add {arguments.group_name}")
        sys.exit(1)
    elif not found_group:
        print_error("group does not exist")
        print()
        print_fix(f"run this command to list available groups:")
        print_fix(f"  $ pdm run lockfile list")
        print_fix()
        print_fix(f"or run this command to add one:")
        print_fix(f"  $ pdm run lockfile add {arguments.group_name}")
        sys.exit(1)

    use_pdm_lockfile(arguments.group_name)


def command_add(arguments: argparse.Namespace) -> None:
    ensure_pdm_lockfile_valid()

    print_info(f"adding lockfile for group '{arguments.group_name}'...")

    result = run_command(
        "pdm",
        "lock",
        "-G",
        str(arguments.group_name),
        "-L",
        get_pdm_lockfile_name(arguments.group_name),
        "--no-cross-platform",
        "--skip=:pre",
    )

    if result:
        print_info("successfully added lockfile")
    else:
        print_error("unable to add lockfile")
        sys.exit(1)

    use_pdm_lockfile(arguments.group_name)

    result = run_command("pdm", "install", "--skip=:pre")

    if result:
        print_info("successfully added lockfile")
    else:
        print_error("unable to add lockfile")
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser()

    argument_subparsers = argument_parser.add_subparsers(title="subcommands")

    argument_parser_check = argument_subparsers.add_parser("check")
    argument_parser_check.set_defaults(func=command_check)

    argument_parser_list = argument_subparsers.add_parser("list")
    argument_parser_list.set_defaults(func=command_list)

    argument_parser_use = argument_subparsers.add_parser("use")
    argument_parser_use.set_defaults(func=command_use)

    argument_parser_use.add_argument("group_name", type=str)

    argument_parser_add = argument_subparsers.add_parser("add")
    argument_parser_add.set_defaults(func=command_add)

    argument_parser_add.add_argument("group_name", type=str)

    return argument_parser


def main() -> None:
    argument_parser = create_argument_parser()

    arguments = argument_parser.parse_args()

    arguments.func(arguments)


if __name__ == "__main__":
    main()
