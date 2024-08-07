"""
Script to check the spelling of one, many or all .po files based
on the custom dictionaries under the 'dictionaries/' directory.
"""

import os
from pathlib import Path
import sys
import tempfile

import pospell


def check_spell(po_files=None):
    """
    Check spell in the given list of po_files and log the spell errors details.

    If no po_files are given, check spell in all files.

    args:
        po_files: list of po_files paths.

    returns:
        - int: spell errors count.

    """
    # Read custom dictionaries
    entries = set()
    for filename in Path("dictionaries").glob("*.txt"):
        with open(filename, "r") as f:
            entries.update(
                stripped_line
                for stripped_line in (line.strip() for line in f.readlines())
                if stripped_line
            )

    # Write merged dictionary file
    with tempfile.NamedTemporaryFile(suffix="_merged_dict.txt") as named_tmp_file:
        for e in entries:
            named_tmp_file.write(f"{e}\n".encode())

        named_tmp_file.flush()
        os.fsync(named_tmp_file.fileno())

        named_tmp_file.seek(0)

        # Run pospell either against all files or the file given on the command line
        if not po_files:
            po_files = Path(".").glob("*/*.po")

        detected_errors = pospell.spell_check(
            po_files, personal_dict=named_tmp_file.name, language="el_GR"
        )
    return detected_errors


if __name__ == "__main__":
    po_files = sys.argv[1:]
    errors = check_spell(po_files)
    sys.exit(0 if errors == 0 else -1)
