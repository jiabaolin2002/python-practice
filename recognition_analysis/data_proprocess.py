import csv
from collections import Counter

CONDITIONS = {1: "Baseline", 2: "Novel", 3: "Revisit", 4: "Control"}

# Responses that have four options: 1, 2, 3, 4
RESPONSES = {"1": 1, "1!": 1, "2": 2, "2@": 2,
             "3": 3, "3#": 3, "4": 4, "4$": 4}


def read_table(path, delimiter):
    """
    Opens a delimited text file and return its rows as a list of
    dictionaries

    Inputs:
        path (str): a file path for the text
        delimiter (str): a delimiter that separates the text file's contents

    Returns: a list of dictionaries, where each dictionary is one row from the
        text file
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def integer(value):
    """
    Convert a value into an integer

    Inputs:
        value (float): value

    Raises:
        ValueError: if the value cannot be converted to an integer

    Returns (int): value
    """
    number = float(value)
    if not number.is_integer():
        raise ValueError(f" {value!r}")
    return int(number)


def load_trials(stimulus_path, log_path, run=1):
    """
    Reads the stimulus file and the experiment log. Filter the stimulus file's
    rows to only that selected run and pair each stimulus record with mathcing
    log row.
    
    Inputs:
        stimulus_path (str): the path to the stimulus file 
        log_path (str): the path to the log file 
        run (int): the selected run
    
    Returns: a list of dictionaries, where each dictionary is one trial 
        containing type, condition, and resposne
    """
    stimuli = [r for r in read_table(stimulus_path, "\t")
               if integer(r["Run"]) == run]
    log = read_table(log_path, "\t")
    if not stimuli or len(stimuli) != len(log):
        raise ValueError(" Run" )
    if [integer(r["Trial"]) for r in log] != list(range(1, len(log) + 1)):
        raise ValueError(" Trial  1 ")
    old_images, trials = {}, []
    for trial, (stim, row) in enumerate(zip(stimuli, log), 1):
        condition = integer(stim["Condition"])
        if condition != integer(row["Condition"]):
            raise ValueError(f"Trial {trial}:  Condition ")
        image = stim["ImageFileName"].strip()
        if not image:
            raise ValueError(f"Trial {trial}: ")
        if condition in CONDITIONS:
            if trials or integer(stim["Phase"]) != 1 or image in old_images:
                raise ValueError(f"Trial {trial}: Phase ")
            old_images[image] = condition
        elif condition == 5:
            if not old_images or integer(stim["Phase"]) != 2:
                raise ValueError(f"Trial {trial}:  Phase ")
            raw = row["Response"].strip()
            if raw and raw not in RESPONSES:
                raise ValueError(f"Trial {trial}:  {raw!r}")
            trials.append({"type": "old" if image in old_images else "new",
                           "condition": old_images.get(image),
                           "response": RESPONSES.get(raw)})
        else:
            raise ValueError(f"Trial {trial}:  Condition {condition}")
    if not trials:
        raise ValueError("Error")
    return trials