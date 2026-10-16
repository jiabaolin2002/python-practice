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

import sys
import argparse
from data_proprocess import *
from calculation import *

def analyze(trials):
    """
    Takes all cleaned trials and computes results for each of the four encoding
    conditions.
    
    Inputs:
        trials: a list of dictionaries, where each dict represents one trial
          containing type, condition, response
    
    Returns: a list of dictionaries, one dictioanry per condition-confidence
        pair
    """
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
