#!/usr/bin/env python3
#
# This script aims to create all issues require to translate a
# specific Python version docs. The flow of the script is very simple:
#
# 1. A list with all the repo's filenames ending in ".po" will be created.
# 2. All already existing issues will be fetched from github.
# 3. If a filename has already an issue for this specific python version,
#    will be excluded.
# 4. All required labels and milestones will be fetched from github.
# 5. If the filename is inside a required dir will get the mvp milestone.
#    Otherwise it will get the additional one.
# 6. An issue will be created in github.
#
# User input:
#
# (required) GITHUB_TOKEN: fine-grained token which is owned by the pygreece
# organization.
# (optional) GITHUB_ADDITIONAL_MILESTONE: the id of the milestone for additional
# files of this version. Default value is 3.
# (optional) GITHUB_MVP_MILESTONE: the id of the milestone for required translated
# files of this version. Default is 2.
# (optional) GITHUB_REPO: the github repo of the greek python translation. Default
# is pygreece/python-docs-gr.
# (optional) PYTHON_VERSION: the python version that all the issues created will
# scope.
#
# Installation:
#
# In order to install all requirements.txt on the root folder run:
# pip install -r requirements.txt
#
# Run:
#
# In order to run the script run:
# GITHUB_TOKEN=<your-token> (all other inputs) python scripts/create_issues.py

import os
from pathlib import Path

from github import Github
from github.Issue import Issue

GITHUB_ADDITIONAL_MILESTONE = int(os.getenv("GITHUB_ADDITIONAL_MILESTONE", 3))
GITHUB_ISSUE_BODY = """/type translation

## Περιγραφή της εργασίας μετάφρασης

Το αρχείο αυτό θα πρέπει να μεταφραστεί στο 100%.

Η μετεφρασμένη έκδοση του αρχείου θα είναι διαθέσιμη στο https://docs.python.org/el/{python_version}/{urlfile}.
Μέχρι τότε, θα φαίνεται η Αγγλική έκδοσης της σελίδας.

Παρακαλούμε, σχολιάστε μέσα στο issue εάν θέλετε αυτό το αρχείο να ανατεθεί σε σας. Ένα μέλος της διαχειριστικής ομάδας θα σας το αναθέσει το συντομότερο δυνατό, ώστε να μπορέσεται να το δουλέψετε.

Θυμηθείτε να ακουληθείσεται τις οδηγίες στον [οδηγό συνεισφοράς](https://github.com/pygreece/python-docs-gr/blob/main/CONTRIBUTING.md)
"""
GITHUB_MVP_MILESTONE = int(os.getenv("GITHUB_MVP_MILESTONE", 2))
GITHUB_REPO = os.getenv("GITHUB_REPO", "pygreece/python-docs-gr")
GITHUB_SEVERITY_MAJOR_LABEL = "severity/major"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.12")
REQUIRED_DIRS = [
    "tutorial/",
    "library/stdtypes.po",
    "library/functions.po",
]


def get_filenames() -> list[str]:
    filenames = []
    current_path = Path.cwd()
    base_path = os.getcwd()
    for path, _, files in os.walk(current_path):

        if "venv" in path:
            continue

        for name in files:
            if name.endswith(".po"):
                filenames.append(os.path.join(path, name).replace(f"{base_path}/", ""))

    print(f"found {len(filenames)} filenames ending with .po")
    return filenames


def filter_already_parsed_filenames(
    filenames: list[str], gh_issues: list[Issue]
) -> list[str]:
    """
    filters filenames having an already created issue. Returns a
    list having only filenames without an issue created in github
    """
    filtered_filenames = []
    for filename in filenames:
        for issue in gh_issues:
            # check if filename is in title AND that the issue is for the same python version
            if filename in issue.title and PYTHON_VERSION in issue.title:
                print(
                    f"Skipping {filename}. There is a similar issue already created at {issue.html_url}"
                )
                break
        else:
            filtered_filenames.append(filename)

    print(f"found {len(filtered_filenames)} filenames without issue")
    return filtered_filenames


def main() -> None:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    # get all filenames of po files inside the repo
    raw_filenames = get_filenames()

    # get all github issues
    issues = repo.get_issues(state="all")

    # filter filenames that have already a github issue assigned
    filenames = filter_already_parsed_filenames(raw_filenames, issues)

    # get milestones and labels to enrich new issues
    gh_mvp_milestone = repo.get_milestone(GITHUB_MVP_MILESTONE)
    gh_additional_milestone = repo.get_milestone(GITHUB_ADDITIONAL_MILESTONE)
    gh_severity_major_label = repo.get_label(GITHUB_SEVERITY_MAJOR_LABEL)

    for filename in filenames:
        title = f"[{PYTHON_VERSION}] Translate `{filename}`"
        urlfile = filename.replace(".po", ".html")

        # if the filename is inside the required dirs for translation
        # add the mvp milestone otherwise add the additional one
        if any(req_dir in title for req_dir in REQUIRED_DIRS):
            milestone = gh_mvp_milestone
        else:
            milestone = gh_additional_milestone

        # create github issue for this file
        issue = repo.create_issue(
            title=title,
            body=GITHUB_ISSUE_BODY.format(
                python_version=PYTHON_VERSION, urlfile=urlfile
            ),
            milestone=milestone,
            labels=[gh_severity_major_label],
        )
        print(f'Issue "{title}" created at {issue.html_url}')


if __name__ == "__main__":
    main()
