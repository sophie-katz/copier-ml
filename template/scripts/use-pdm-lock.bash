#!/bin/bash

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

set -e

PDM_GROUPS="$1"

if [ -z "$1" ]; then
    echo "usage: $0 <PDM GROUP>"
    echo
    echo "available groups:"
    for i in pdm.*.lock; do
        echo "  $(echo $i | cut -d '.' -f 2)"
    done
    exit 1
fi

if [ -f "pdm.lock" ] && [ "$(stat --format="%F" "pdm.lock")" != "symbolic link" ]; then
    echo "error: 'pdm.lock' must be a symbolic link"
    echo
    echo "fix: delete or move it and try again"
    exit 1
fi

if [ ! -f "pdm.${PDM_GROUPS}.lock" ]; then
    echo "error: a valid group must be used - available groups are:"
    for i in pdm.*.lock; do
        echo "  $(echo $i | cut -d '.' -f 2)"
    done
    echo
    echo "note: they are all located in '$(pwd)' with filenames 'pdm.<GROUP>.lock'. 'pdm.${PDM_GROUPS}.lock' does not exist."
    exit 1
fi

ln -sf "pdm.${PDM_GROUPS}.lock" "pdm.lock"
