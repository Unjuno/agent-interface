#!/usr/bin/env python3
"""Post-formal mutation checks; never invokes candidate/auditor CLI or container."""
import copy
import json
from pathlib import Path

import audit

ROOT = Path(__file__).parent
fixture = json.loads((ROOT / "INPUT.json").read_text())
candidate = json.loads((ROOT / "formal_02/candidate.json").read_text())
cases = {c["case_id"]: c for c in fixture["cases"]}
results = {(r["case_id"], r["method"]): r for r in candidate["results"]}

def rejected(case_id, changed):
    case = cases[case_id]
    assert audit.check_one(case, "dependency_aware", changed), case_id

# Deleting surface_origin -> screen_position would miss this transitive change;
# falsely preserving both old derived values must be detected by the oracle.
mutant = copy.deepcopy(results[("transitive_layout_and_sibling", "dependency_aware")])
mutant["fields"]["screen_position"] = {"status": "CURRENT", "value": [44, 55]}
mutant["fields"]["recovery_anchor"] = {"status": "CURRENT", "value": "pane-C@44,55#doc-8"}
rejected("transitive_layout_and_sibling", mutant)

# A mode-branch mutation cannot preserve enabled from the old edit branch.
mutant = copy.deepcopy(results[("mode_dependent_branch", "dependency_aware")])
mutant["fields"]["enabled"] = {"status": "CURRENT", "value": True}
rejected("mode_dependent_branch", mutant)

# An old-generation event may not be moved into the accepted receipt.
mutant = copy.deepcopy(results[("object_id_reuse_new_generation", "dependency_aware")])
mutant["rejected_events"] = [e for e in mutant["rejected_events"] if e["event_id"] != "late-old-generation-6"]
mutant["accepted_events"].append({"event_id": "late-old-generation-6", "status": "ACCEPTED"})
rejected("object_id_reuse_new_generation", mutant)

# Unsupported current claims remain invalid even if their numeric value looks plausible.
mutant = copy.deepcopy(results[("missing_source_and_dependency_coverage", "dependency_aware")])
mutant["fields"]["screen_position"] = {"status": "CURRENT", "value": [62, 74]}
rejected("missing_source_and_dependency_coverage", mutant)

print("SUPPLEMENTAL_MUTATION_CONTROLS_PASS 4/4")
