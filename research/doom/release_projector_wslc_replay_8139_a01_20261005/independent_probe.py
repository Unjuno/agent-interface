import json

from project_v39_release_measurement_v1 import project
from test_project_v39_release_measurement_v1 import valid_pair


def check(name, mutate=None):
    rows = valid_pair()
    if mutate is not None:
        mutate(rows)
    result = project(rows)
    return {"case": name, "ready": result["measurement_ready"],
            "row_count": len(result["rows"])}


results = [
    check("untouched_positive"),
    check("attempt_true_only", lambda rows: rows[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0].update(attempt=True)),
    check("release_identity_step_true_only", lambda rows: rows[1].update(step=True)),
    check("release_batch_step_true_only", lambda rows: rows[1].update(release_batch_step=True)),
]
print(json.dumps(results, sort_keys=True))

