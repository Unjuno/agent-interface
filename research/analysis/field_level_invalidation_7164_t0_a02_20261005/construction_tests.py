#!/usr/bin/env python3
"""Pre-freeze construction checks; not a formal candidate or audit run."""
import json
from pathlib import Path
import candidate
import audit

HERE = Path(__file__).parent
schema = json.loads((HERE / "SCHEMA.json").read_text())
fixture = json.loads((HERE / "INPUT.json").read_text())
cases = {c["case_id"]: c for c in fixture["cases"]}

def result(case, method):
    return candidate.apply_case(cases[case], schema, method)

# Formula and transitive propagation.
r = result("transitive_layout_and_sibling", "dependency_aware")
assert r["fields"]["screen_position"] == {"status": "CURRENT", "value": [49, 62]}
assert r["fields"]["recovery_anchor"] == {"status": "CURRENT", "value": "pane-C@49,62#doc-8"}
assert r["fields"]["object_caption"]["value"] == "Open|Report"

# Dynamic dependency branch follows the new mode.
r = result("mode_dependent_branch", "dependency_aware")
assert r["fields"]["enabled"] == {"status": "CURRENT", "value": False}

# Old epochs and prior identity generations are rejected.
r = result("delayed_older_update", "whole_record")
assert [x["event_id"] for x in r["rejected_events"]] == ["late-2"]
r = result("object_id_reuse_new_generation", "whole_record")
assert r["key"]["generation"] == 5
assert [x["event_id"] for x in r["rejected_events"]] == ["late-old-generation-6"]
assert r["fields"]["surface_id"] == {"status": "CURRENT", "value": "pane-new"}
assert r["fields"]["surface_origin"]["status"] == "UNKNOWN"

# Incomplete source/dependency coverage may not leave current derived claims.
r = result("missing_source_and_dependency_coverage", "dependency_aware")
assert all(r["fields"][n]["status"] == "UNKNOWN" for n in schema["derived_order"])

# The deliberately weak method must expose stale layout state.
weak = result("transitive_layout_and_sibling", "independent_field")
assert weak["fields"]["screen_position"]["value"] == [44, 55]
assert weak["fields"]["recovery_anchor"]["value"] == "pane-C@44,55#doc-8"

# Independently authored oracle matches fully refreshed methods and catches
# direct-field-only staleness without importing candidate implementation.
for case_id in ("parent_surface_replacement", "transitive_layout_and_sibling",
                "mode_dependent_branch", "delayed_older_update"):
    c = cases[case_id]
    assert not audit.check_one(c, "whole_record", result(case_id, "whole_record"))
    assert not audit.check_one(c, "dependency_aware", result(case_id, "dependency_aware"))
assert audit.check_one(cases["transitive_layout_and_sibling"], "independent_field", weak)

# Mutation controls reject corrupted derivations, false CURRENT under missing
# support, wrong dynamic branch, and forged acceptance receipts.
baseline = result("mode_dependent_branch", "dependency_aware")
mutant = json.loads(json.dumps(baseline))
mutant["fields"]["enabled"] = {"status": "CURRENT", "value": True}
assert audit.check_one(cases["mode_dependent_branch"], "dependency_aware", mutant)
incomplete = result("missing_source_and_dependency_coverage", "dependency_aware")
mutant = json.loads(json.dumps(incomplete))
mutant["fields"]["screen_position"] = {"status": "CURRENT", "value": [1, 2]}
assert audit.check_one(cases["missing_source_and_dependency_coverage"], "dependency_aware", mutant)
delayed = result("delayed_older_update", "whole_record")
mutant = json.loads(json.dumps(delayed))
mutant["rejected_events"] = []
assert audit.check_one(cases["delayed_older_update"], "whole_record", mutant)

# The six-case fixture's expected complete reducers agree with the oracle;
# the negative comparator is allowed to fail only as a stale-value witness.
for cid, c in cases.items():
    assert not audit.check_one(c, "whole_record", result(cid, "whole_record")), cid
    assert not audit.check_one(c, "dependency_aware", result(cid, "dependency_aware")), cid
weak_errors = audit.check_one(cases["transitive_layout_and_sibling"], "independent_field", weak)
assert any("screen_position" in error for error in weak_errors)

print("CONSTRUCTION_TESTS_PASS")
