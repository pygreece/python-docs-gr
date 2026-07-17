"""
Script to check the spelling of one, many or all .po files based
on the custom dictionaries under the 'dictionaries/' directory.

Gives the option to print the detected errors and add new entries to the dictionary file.

Display information about usage with `python scripts/check_spelling.py --help`
"""

import argparse
import contextlib
import functools
import os
import multiprocessing
from pathlib import Path
import sys
import tempfile

import pospell


def main():
    parser = create_parser()
    args = parser.parse_args()

    errors = check_spell(args.po_files)

    if args.print_errors:
        print_errors(errors)

    if args.write_entries:
        write_new_entries({e[-1] for e in errors})

    sys.exit(0 if len(errors) == 0 else -1)


def create_parser():
    """
    Creates and configures the command line argument parser.

    returns:
        - argparse.ArgumentParser: the argument parser containing the passed arguments and flags.
    """
    parser = argparse.ArgumentParser(
        usage="python check_spelling.py [options]",
        description="spell-check translated .po files and add new entries to the dictionary if needed.",
    )

    parser.add_argument(
        "-p",
        "--print-errors",
        action="store_true",
        dest="print_errors",
        help="print the detected errors of the spell-check",
    )
    parser.add_argument(
        "-w",
        "--write-entries",
        action="store_true",
        dest="write_entries",
        help="write the new detected entries in the dictionary file",
    )
    parser.add_argument(
        "-f",
        "--po-files",
        dest="po_files",
        nargs="*",
        default=list(),
        help="list of .po files to spell-check, if not given checks all po files",
    )

    return parser


def check_spell(po_files):
    """
    Check spell in the given list of po_files.

    args:
        po_files: list of po_files paths.

    returns:
        - list: list of tuples containing detected errors.
    """
    entries = read_dictionary_entries()

    with write_entries_to_tmp_file(entries) as named_tmp_file:

        # Run pospell either against all files or the files given on the command line
        if len(po_files) == 0:
            po_files = Path(".").glob("*/*.po")

        detected_errors = detect_errors(po_files, named_tmp_file.name)
    return detected_errors


def read_dictionary_entries():
    """
    Read the entries in the dictionary files under `dictionaries` directory.

    returns:
        - set: a set of string entries
    """
    entries = set()
    dictionaries = Path("dictionaries").glob("*.txt")

    for filename in dictionaries:
        with open(filename, "r") as f:
            entries.update(
                stripped_line
                for stripped_line in (line.strip() for line in f.readlines())
                if stripped_line
            )

    return entries


@contextlib.contextmanager
def write_entries_to_tmp_file(entries):
    """
    Write the given entries to a named temporary file and yield the file.

    args:
        entries: a set of entries (strings) to write to the temporary file.

    returns:
        - tempfile.NamedTemporaryFile: the temporary file with the given entries.
    """
    with tempfile.NamedTemporaryFile(suffix="_merged_dict.txt") as named_tmp_file:
        for e in entries:
            named_tmp_file.write(f"{e}\n".encode())

        named_tmp_file.flush()
        os.fsync(named_tmp_file.fileno())

        named_tmp_file.seek(0)

        yield named_tmp_file


# Clone of pospell.spell_check tailored to current needs.
# source: https://git.afpy.org/AFPy/pospell/src/branch/main/pospell.py
def detect_errors(po_files, personal_dict):
    """
    Check for spelling mistakes in the given po_files.

    args:
        po_files: list of strings or Path objects pointing to po files.
        personal_dict: name of file containing dictionary entries.

    returns:
        - list: a list of tuples with the detected errors
    """
    # Pool.__exit__ calls terminate() instead of close(), we need the latter,
    # which ensures the processes' atexit handlers execute fully, which in
    # turn lets coverage write the sub-processes' coverage information
    jobs = os.cpu_count()
    pool = multiprocessing.Pool(jobs)

    try:
        input_lines = pospell.flatten(
            pool.map(
                functools.partial(pospell.po_to_text, drop_capitalized=False),
                po_files,
            )
        )

        if not input_lines:
            return []

        # Distribute input lines across workers
        lines_per_job = (len(input_lines) + jobs - 1) // jobs
        chunked_inputs = [
            input_lines[i : i + lines_per_job]
            for i in range(0, len(input_lines), lines_per_job)
        ]
        errors = pospell.flatten(
            pool.map(
                functools.partial(pospell.run_hunspell, "el_GR", personal_dict),
                chunked_inputs,
            )
        )
    finally:
        pool.close()
        pool.join()

    return errors


def print_errors(errors):
    """
    Print the given errors with the following format:
    filename:linenumber:word

    args:
        errors: list of tuples with detected errors.
    """
    if len(errors) > 0:
        print("\nDetected errors:")

    for error in errors:
        print("\t" + ":".join(map(str, error)))


def write_new_entries(new_entries):
    """
    Write the given entries to the dictionary file respecting the
    alphabetical sorting.

    args:
        new_entries: set of entries (strings) to write to the dictionary file.
    """
    entries = read_dictionary_entries()

    entries.update(new_entries)
    entries = list(entries)
    entries.sort()

    with open(Path("dictionaries", "main.txt"), "w") as file:
        for e in entries:
            file.write(e+"\n")

    if len(new_entries) > 0:
        print("\nWrote the below new entries to main.txt:")

    for e in new_entries:
        print(f"\t {e}")


if __name__ == "__main__":
    main()
