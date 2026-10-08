import json
from candidate import POLICIES, run
from auditor import expected_record

cases=json.load(open("input/cases.json",encoding="utf-8"))["cases"]
rows=run("input/cases.json")
assert len(rows)==32 and len({(r["case"],r["policy"]) for r in rows})==32
for case in cases:
    for policy in POLICIES:
        row=next(r for r in rows if (r["case"],r["policy"])==(case["id"],policy))
        assert row==expected_record(case,policy)
by={(r["case"],r["policy"]):r for r in rows}
assert by[("selection_autosave_coupling","RESTORE_ONLY")]["effects_lost"]
assert not by[("selection_autosave_coupling","RESTORE_PLUS_DIFF")]["effects_lost"]
assert by[("external_viewport_change","RESTORE_ONLY")]["external_overwrite"]
assert not by[("external_viewport_change","RESTORE_PLUS_DIFF")]["external_overwrite"]
assert by[("required_download_evidence","RESTORE_ONLY")]["artifacts_lost"]
assert not by[("required_download_evidence","RESTORE_PLUS_DIFF")]["artifacts_lost"]
assert by[("hidden_modal_held_input","RESTORE_ONLY")]["unresolved_cleared"]
assert not by[("hidden_modal_held_input","RESTORE_PLUS_DIFF")]["unresolved_cleared"]
print("BUILD_PASS cases=8 policies=4 rows=32 adversarial_controls=4")
