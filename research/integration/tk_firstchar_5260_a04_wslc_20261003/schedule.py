"""Deterministic factorial schedule shared by candidate and auditor."""
import random


def schedule(fixture):
    rows = []
    for method in fixture["coordinate_methods"]:
        for delay in fixture["first_key_delay_ms"]:
            for load in fixture["load_conditions"]:
                for replicate in range(fixture["replicates_per_cell"]):
                    rows.append({"coordinate_method": method, "first_key_delay_ms": delay,
                                 "load": load, "replicate": replicate})
    random.Random(fixture["seed"]).shuffle(rows)
    return rows
