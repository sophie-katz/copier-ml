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

import os
import sys
import re

PDM_LOCK_PATTERN = re.compile(r"pdm\.([^.]+)\.lock")

if len(sys.argv) == 0:
    print("usage: python3 scripts/use_pdm_lock.py <PDM GROUP>")
    print()
    print("available groups:")

    for i in os.listdir():
        match = PDM_LOCK_PATTERN.match(i)
        if match:
            print(f"  {match.group(1)}")

    sys.exit(1)

if os.path.exists("pdm.lock") and not os.path.islink("pdm.lock"):
    print("error: 'pdm.lock' must be a symbol link")
    print()
    print("fix: delete or move it and try again")
    sys.exit(1)

if not os.path.exists(f"pdm.{sys.argv[1]}.lock"):
    print("error: a valid group must be used - available groups are:")

    for i in os.listdir():
        match = PDM_LOCK_PATTERN.match(i)
        if match:
            print(f"  {match.group(1)}")

    print()
    print(
        f"note: they are all located in '{os.getcwd()}' with filenames 'pdm.<GROUP>.lock'. 'pdm.{sys.argv[1]}.lock' does not exist."
    )
    sys.exit(1)

if os.path.exists("pdm.lock"):
    os.remove("pdm.lock")

os.symlink(f"pdm.{sys.argv[1]}.lock", "pdm.lock")
