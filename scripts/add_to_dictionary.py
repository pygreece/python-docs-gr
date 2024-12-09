"""
Script to update the custom dictionary 'main.txt' with new words from a given .po file.

The script scans a specified .po file, ignoring certain metadata lines (e.g., lines starting with "#:").
It extracts all unique Greek and English words, compares them against the custom dictionary
under the 'dictionaries/' directory (sibling to the 'scripts/' directory), and adds any new words in alphabetical order.
"""

import sys
import os
import re

def scan_and_update(file_path):
    """
    Scan the given .po file, extract words, and update the main dictionary.

    If the dictionary does not exist, it creates a new one.

    Args:
        file_path (str): Path to the .po file.

    Returns:
        int: The number of new words added to the dictionary.
    """
    # Define the path to the main.txt file relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the parent directory of scripts/ and then to dictionaries/
    dictionaries_dir = os.path.abspath(os.path.join(script_dir, "..", "dictionaries"))
    dictionary_path = os.path.join(dictionaries_dir, "main.txt")

    # Step 1: Ensure the dictionaries directory exists
    os.makedirs(dictionaries_dir, exist_ok=True)

    # Step 2: Read and sort the existing dictionary
    try:
        with open(dictionary_path, 'r', encoding='utf-8') as dict_file:
            dictionary = set(line.strip().lower() for line in dict_file if line.strip())
    except FileNotFoundError:
        print(f"Dictionary file not found at {dictionary_path}. Creating a new one.")
        dictionary = set()

    # Step 3: Open the input .po file
    try:
        with open(file_path, 'r', encoding='utf-8') as input_file:
            lines = input_file.readlines()
    except FileNotFoundError:
        print(f"Input file {file_path} not found.")
        return 0

    # Regular expression to ignore metadata lines like #: reference/executionmodel.rst:145
    ignore_pattern = re.compile(r"^#:")

    # Regular expression to include accented Greek letters
    word_pattern = re.compile(r'\b[a-zA-Zα-ωά-ώΑ-ΩΆ-Ώ]+\b', re.UNICODE)

    new_words = set()
    entry_buffer = []
    collecting_msgstr = False

    # Step 4: Extract words from the .po file
    for line in lines:
        if ignore_pattern.match(line):
            continue  # Ignore metadata lines

        # Handle msgstr entries
        if line.startswith("msgstr"):
            collecting_msgstr = True
            # Extract the content after 'msgstr' and remove surrounding quotes
            msgstr_content = line.strip().partition('msgstr')[2].strip().strip('"')
            if msgstr_content:
                entry_buffer.append(msgstr_content)
        elif collecting_msgstr:
            if line.strip() == "" or not line.startswith('"'):
                # End of msgstr block
                collecting_msgstr = False
                if entry_buffer:
                    full_text = " ".join(entry_buffer)
                    words = word_pattern.findall(full_text)
                    # Add unique new words in lowercase
                    new_words.update(word.lower() for word in words if word.lower() not in dictionary)
                    entry_buffer = []
            else:
                # Continue collecting multiline msgstr
                # Remove surrounding quotes and append
                entry_buffer.append(line.strip().strip('"'))

    # Handle any remaining buffered text after the loop
    if collecting_msgstr and entry_buffer:
        full_text = " ".join(entry_buffer)
        words = word_pattern.findall(full_text)
        new_words.update(word.lower() for word in words if word.lower() not in dictionary)

    # Step 5: Update the dictionary with new words
    if new_words:
        dictionary.update(new_words)
        # Sort and write back to the dictionary file
        sorted_dictionary = sorted(dictionary)
        with open(dictionary_path, 'w', encoding='utf-8') as dict_file:
            dict_file.write("\n".join(sorted_dictionary))
        print(f"Added {len(new_words)} new word{'s' if len(new_words) != 1 else ''} to the dictionary.")
    else:
        print("No new words to add to the dictionary.")

    # Return the count of new words added
    return len(new_words)

if __name__ == "__main__":
    # Check if the script received the correct number of arguments
    if len(sys.argv) != 2:
        print("Usage: python add_to_dictionary.py <file_path>")
    else:
        file_path = sys.argv[1]
        # Validate that the provided path is a file
        if not os.path.isfile(file_path):
            print(f"The provided path '{file_path}' is not a valid file.")
            sys.exit(1)
        # Process the input file and update the dictionary
        new_word_count = scan_and_update(file_path)

