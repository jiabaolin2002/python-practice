from statistics import NormalDist
import math

def calculate_dprime(old_responses, new_responses):
    """
    Compute d-prime for one subset of responses.
    
    Inputs:
        old_response: a list of old values
        new_response: a list of new values
    
    Returns: a dictionary of raw counts containing misses (int), correct 
    rejection (int), sample sizes (int), and the d' values (float)
    """
    n_old, n_new = len(old_responses), len(new_responses)
    hits = sum(r in (3, 4) for r in old_responses)
    false_alarms = sum(r in (3, 4) for r in new_responses)
    h = (hits + 0.5) / (n_old + 1) if n_old else math.nan
    f = (false_alarms + 0.5) / (n_new + 1) if n_new else math.nan
    d = NormalDist().inv_cdf(h) - NormalDist().inv_cdf(f) if n_old and n_new else math.nan
    return dict(n_old=n_old, n_new=n_new, hits=hits, misses=n_old-hits,
                false_alarms=false_alarms, correct_rejections=n_new-false_alarms,
                hit_rate_corrected=h, false_alarm_rate_corrected=f, dprime=d)