#!/usr/bin/env python3
#
# This script aims to create all issues require to translate a
# specific Python version docs. The flow of the script is very simple.
#
# User input:
#
# (optional) GITHUB_ADDITIONAL_MILESTONE: the id of the milestone for additional
# files this version. Default value is 3
#
# (optional) GITHUB_MVP_MILESTONE:
GITHUB_REPO = os.getenv("GITHUB_REPO", "pygreece/python-docs-gr")
GITHUB_SEVERITY_MAJOR_LABEL = "severity/major"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.12")
REQUIRED_DIRS = ["tutorial/", "library/stdtypes", "library/functions"]

#
# Env setup:
# The script creates all the temporary directories and exports
# the GNUPGHOME environment variable in order to avoid creating
# issues to the operating system which is hosting the process.
# It also updates the ownership and mode of these directories
# in order to be able to clean them afterwards
#
# Master-key/Sub-keys generation:
# Following the environment setup the script will try to
# create the pubring.kbx file and with this the master key
# of the user. After the master key generation inside the custom homedir
# we are going to create three (3) sub keys for the newly
# created key. Those keys have specific usage and this is
# sign (signing) | encr (encryption) | auth (authentication)
#
# Card (YubiKey Reset & Re-configure)
# With --card-edit command and the usage of pexpect we are reseting
# and reconfiguring the card with the created master and sub keys.
# Moreover, the script applies a factory-reset command and then
# It imports the keys and the given input to the card
#
# Revocation certificate/ssh key/public key export:
# As a last step it generates the revocation certificate,
# and exportd the ssh_key and public key for the user
import os
from pathlib import Path

from github import Github
from github.Issue import Issue
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)

GITHUB_ADDITIONAL_MILESTONE = int(os.getenv("GITHUB_ADDITIONAL_MILESTONE", 3))
GITHUB_MVP_MILESTONE = int(os.getenv("GITHUB_ADDITIONAL_MILESTONE", 2))
GITHUB_REPO = os.getenv("GITHUB_REPO", "pygreece/python-docs-gr")
GITHUB_SEVERITY_MAJOR_LABEL = "severity/major"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.12")
REQUIRED_DIRS = ["tutorial/", "library/stdtypes", "library/functions"]


def get_filenames() -> list[str]:
    filenames = []
    current_path = Path.cwd()
    base_path = os.getcwd()
    for path, _, files in os.walk(current_path):
        for name in files:
            if name.endswith(".po"):
                filenames.append(os.path.join(path, name).replace(f"{base_path}/", ""))

    logging.info(f"found {len(filenames)} filenames ending with .po")
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
        issue_already_exists = False

        for issue in gh_issues:
            # check if filename is in title AND that the issue is for the same python version
            if filename in issue.title and PYTHON_VERSION in issue.title:
                logging.info(
                    f"Skipping {filename}. There is a similar issue already created at {issue.html_url}"
                )
                issue_already_exists = True
                break

        if not issue_already_exists:
            filtered_filenames.append(filename)

    logging.info(f"found {len(filtered_filenames)} filenames without issue")
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
            body=f"""/type translation

## Περιγραφή της εργασίας μετάφρασης

Το αρχείο αυτό θα πρέπει να μεταφραστεί στο 100%.

Η μετεφρασμένη έκδοση του αρχείου θα είναι διαθέσιμη στο https://docs.python.org/el/3.12/{urlfile}.
Μέχρι τότε, θα φαίνεται η Αγγλική έκδοσης της σελίδας.

Παρακαλούμε, σχολιάστε μέσα στο issue εάν θέλετε αυτό το αρχείο να ανατεθεί σε σας. Ένα μέλος της διαχειριστικής ομάδας θα σας το αναθέσει το συντομότερο δυνατό, ώστε να μπορέσεται να το δουλέψετε.

Θυμηθείτε να ακουληθείσεται τις οδηγίες στον [οδηγό συνεισφοράς](https://github.com/pygreece/python-docs-gr/blob/main/CONTRIBUTING.md)
""",
            milestone=milestone,
            labels=[gh_severity_major_label],
        )
        logging.info(f'Issue "{title}" created at {issue.html_url}')


if __name__ == "__main__":
    main()
