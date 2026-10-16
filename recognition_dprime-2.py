"""Compute sure and unsure d-prime for four encoding conditions.
Requires Python 3.8+; no third-party packages.

Usage: python recognition_dprime.py stimulus.txt experiment_log.txt --run 1
Append > results.csv to save the output as CSV.
Process one participant and one run at a time. After filtering by Run,
stimulus rows must match the actual presentation order and the complete log.
Log Trial numbers must start at 1 and be consecutive.

Encoding conditions: 1=Baseline, 2=Novel, 3=Revisit, 4=Control.
Recognition condition: 5. Images seen during encoding are Old; others are New.
All four groups share the New trials. Sure uses responses 1/4 (4=Old);
unsure uses 2/3 (3=Old). Each confidence subset has its own denominators
and shared false-alarm rate. These are confidence-conditional d-prime values,
not meta-d-prime or threshold estimates using all trials as denominators.
Rates use (count+0.5)/(total+1). Missing Old or New data produce nan.
Blank responses are counted separately and excluded; unknown responses raise
an error. RT=2.000 is not automatically excluded.
Response counts and missing counts describe the unfiltered data and are
repeated in both confidence rows.
"""

import argparse
import csv
import math
import sys
from collections import Counter
from statistics import NormalDist


CONDITIONS = {1: "Baseline", 2: "Novel", 3: "Revisit", 4: "Control"}
RESPONSES = {"1": 1, "1!": 1, "2": 2, "2@": 2,
             "3": 3, "3#": 3, "4": 4, "4$": 4}


def read_table(path, delimiter):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def integer(value):
    number = float(value)
    if not number.is_integer():
        raise ValueError(f" {value!r}")
    return int(number)


def load_trials(stimulus_path, log_path, run=1):
    """Join rows in presentation order and recover encoding conditions by image name."""
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


def calculate_dprime(old_responses, new_responses):
    """Return counts, corrected rates, and d-prime from confidence-filtered responses."""
    n_old, n_new = len(old_responses), len(new_responses)
    hits = sum(r in (3, 4) for r in old_responses)
    false_alarms = sum(r in (3, 4) for r in new_responses)
    h = (hits + 0.5) / (n_old + 1) if n_old else math.nan
    f = (false_alarms + 0.5) / (n_new + 1) if n_new else math.nan
    d = NormalDist().inv_cdf(h) - NormalDist().inv_cdf(f) if n_old and n_new else math.nan
    return dict(n_old=n_old, n_new=n_new, hits=hits, misses=n_old-hits,
                false_alarms=false_alarms, correct_rejections=n_new-false_alarms,
                hit_rate_corrected=h, false_alarm_rate_corrected=f, dprime=d)


def analyze(trials):
    """Return four conditions by two confidence subsets, including raw response counts."""
    results = []
    for condition, name in CONDITIONS.items():
        old = [t["response"] for t in trials
               if t["type"] == "old" and t["condition"] == condition]
        new = [t["response"] for t in trials
               if t["type"] == "new" ]
        counts = {}
        for kind, responses in (("old", old), ("new", new)):
            counter = Counter(responses)
            counts.update({f"{kind}_response_{r}": counter[r] for r in range(1, 5)})
            counts[f"{kind}_missing"] = counter[None]
        for confidence, keys in (("sure", (1, 4)),
                                 ("unsure", (2, 3))):
            result = dict(condition=condition, condition_name=name,
                          confidence=confidence, new_pool="shared")
            result.update(calculate_dprime([r for r in old if r in keys],
                                          [r for r in new if r in keys]))
            result.update(counts)
            results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stimulus", help="刺激列表 TXT")
    parser.add_argument("log", help="同一次运行的日志 TXT")
    parser.add_argument("--run", type=int, default=1)
    args = parser.parse_args()
    try:
        results = analyze(load_trials(args.stimulus, args.log, args.run))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"typeerror:{exc}\n")
    writer = csv.DictWriter(sys.stdout, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)


if __name__ == "__main__":
    main()
