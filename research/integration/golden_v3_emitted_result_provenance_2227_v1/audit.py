import json
from pathlib import Path

m=json.loads((Path(__file__).with_name("MATRIX.json")).read_text())
assert m["decision"]=="HOLD_FIELD_PROVENANCE_INCOMPLETE"
assert m["model_gui_network_input"]==0
assert m["docker"]=="not_required_for_source_audit"
p=m["field_provenance"]
assert p["schema"]=="emitted_v2_report"
assert p["program_completed"]=="absent_from_frozen_v2_source"
assert p["task_success"]=="absent_from_frozen_v2_source"
assert p["partial_effects"]=="absent_from_frozen_v2_source"
assert p["status"]=="absent_from_frozen_v2_source"
assert p["cleanup_error"]=="absent_from_frozen_v2_source"
print("EMITTED_RESULT_PROVENANCE_AUDIT_PASS_HOLD")
