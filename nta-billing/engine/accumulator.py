"""
Accumulator for multi-order jobs. Keeps a JSON snapshot of every order's
raw quantities that have been added so far in this account/job, so it can
be (a) reloaded if the conversation is lost, and (b) turned into a full
multi-order xlsx (order sheets + a combined ריכוז) on demand.
"""
import json

def new_job():
    return {"orders": [], "meta": {}}

def add_order(job, name, number, raw_values, overrides=None):
    job["orders"] = [o for o in job["orders"] if o["number"] != number]
    job["orders"].append({"name": name, "number": number, "raw": raw_values,
                           "overrides": overrides or {}})
    return job

def set_overrides(job, number, overrides):
    for o in job["orders"]:
        if o["number"] == number:
            o.setdefault("overrides", {}).update(overrides)
            return job
    raise KeyError(f"order {number} not found in job - add it first")

def save_job(job, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=1)

def load_job(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
