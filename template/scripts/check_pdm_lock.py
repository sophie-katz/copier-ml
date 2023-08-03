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

if not os.path.exists("pdm.lock"):
    print(f"error: 'pdm.lock' file must be present in '{os.getcwd()}'")
    print()
    print(
        "fix: use this command to select a lockfile to use, then follow instructions:"
    )
    if sys.platform == "win32":
        print("  > python3 scripts/use_pdm_lock.py")
    else:
        print("  $ python3 scripts/use_pdm_lock.py")
    sys.exit(1)

if not os.path.islink("pdm.lock"):
    print("error: 'pdm.lock' must be a symbolic link")
    print()
    print("fix: delete or move it and try again")
    sys.exit(1)
