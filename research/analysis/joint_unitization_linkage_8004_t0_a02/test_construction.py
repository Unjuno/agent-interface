#!/usr/bin/env python3
"""Development-only oracle checks before the formal freeze and CLI invocation."""
import json
from pathlib import Path
import audit
import candidate

HERE = Path(__file__).parent
public = json.loads((HERE / "public_input.json").read_text())
truth = json.loads((HERE / "auditor_truth.json").read_text())
result = candidate.evaluate(public)
summary = audit.validate(public, truth, result)
diagnostics = audit.linkage_diagnostics(public, truth, result)
mutations = audit.mutation_controls(public, truth, result)
assert all(value == "REJECTED" for value in mutations.values())
for scenario_id in ("joint_boundary_linkage_independent_sources", "joint_boundary_linkage_shared_AB"):
    joint = next(x for x in result["scenarios"] if x["scenario_id"] == scenario_id)
    assert joint["analysis_sets"]["boundary_only"]["lower"] == joint["analysis_sets"]["boundary_only"]["upper"] == 2
    assert joint["analysis_sets"]["linkage_only"]["lower"] == joint["analysis_sets"]["linkage_only"]["upper"] == 2
    assert joint["analysis_sets"]["joint"]["lower"] == 2 and joint["analysis_sets"]["joint"]["upper"] == 3
    assert summary[scenario_id]["all_channel_unobserved_truth_count"] == 1
assert diagnostics["joint_boundary_linkage_shared_AB:split_ambiguous"]["mixed_truth_components"] == 0
assert diagnostics["joint_boundary_linkage_shared_AB:split_ambiguous"]["fragmented_truth_events"] == 0
assert diagnostics["joint_boundary_linkage_shared_AB:split_hard"]["fragmented_truth_events"] == 1
assert diagnostics["joint_boundary_linkage_shared_AB:merged_hard"]["mixed_truth_components"] == 1
print(f"construction PASS: {len(public['scenarios'])} scenarios; {sum(len(x['combinations']) for x in result['scenarios'])} assignments; {len(mutations)} mutations")
