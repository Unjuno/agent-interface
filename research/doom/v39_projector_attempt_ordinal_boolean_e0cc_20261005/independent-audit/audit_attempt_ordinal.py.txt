"""Independent exact-JSON-type adjudication for the V39 ordinal mutation."""
import copy
import json
import hashlib
from pathlib import Path

from project_v39_release_measurement_v1 import project
from test_project_v39_release_measurement_v1 import valid_pair

root = Path(__file__).resolve().parents[1]
source = root.parent / "project_v39_release_measurement_v1.py"
source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
control = valid_pair()
control_ordinal = control[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]["attempt"]
control_expected = type(control_ordinal) is int and control_ordinal == 1
control_actual = project(control)

mutant = copy.deepcopy(control)
mutant[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]["attempt"] = True
mutant_ordinal = mutant[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]["attempt"]
mutant_expected = type(mutant_ordinal) is int and mutant_ordinal == 1
mutant_actual = project(mutant)

result = {
    "scope": "synthetic one-field JSON schema mutation only",
    "projector_sha256": source_sha256,
    "positive_control": {
        "ordinal_type": type(control_ordinal).__name__,
        "independent_exact_int_contract": control_expected,
        "measurement_ready": control_actual["measurement_ready"],
        "projected_rows": len(control_actual["rows"]),
        "pass": control_expected and control_actual["measurement_ready"],
    },
    "boolean_mutation": {
        "ordinal_type": type(mutant_ordinal).__name__,
        "python_equality_to_one": mutant_ordinal == 1,
        "independent_exact_int_contract": mutant_expected,
        "measurement_ready": mutant_actual["measurement_ready"],
        "projected_rows": len(mutant_actual["rows"]),
        "pass": (not mutant_expected and not mutant_actual["measurement_ready"]
                 and mutant_actual["rows"] == []),
    },
}
result["audit_pass"] = (result["positive_control"]["pass"]
                        and result["boolean_mutation"]["pass"])
print(json.dumps(result, indent=2, sort_keys=True))
if not result["audit_pass"]:
    raise SystemExit(1)
