#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).parent
cmds=[
    [sys.executable,str(HERE/"analyzer_a.py"),str(HERE/"INPUT_LEDGER.json"),str(HERE/"RESULT_A.json")],
    [sys.executable,str(HERE/"analyzer_b.py"),str(HERE/"INPUT_LEDGER.json"),str(HERE/"RESULT_B.json")],
    [sys.executable,str(HERE/"audit.py")],
    [sys.executable,str(HERE/"controls.py")],
]
for c in cmds:
    subprocess.run(c,check=True)
audit=json.loads((HERE/"AUDIT.json").read_text())
corr=json.loads((HERE/"CORRUPTION.json").read_text())
formal={
    "task":"MODEL-BRANCH-COST-RETAINED-IDENTIFIABILITY-V2-20260918-001",
    "formal_invocations":1,
    "reruns":0,
    "decision":audit["decision"],
    "audit_pass":audit["audit_pass"],
    "corruption_controls_rejected":corr["rejected"],
    "corruption_controls_total":corr["total"],
    "admissible_pair_count":audit["admissible_pair_count"],
    "same_image_pairs":audit["same_image_pairs"],
    "candidate_pairs":audit["candidate_pairs"],
    "causal_per_branch_estimate":None,
    "model_calls":0,
    "gui_actions":0,
    "task_input_actions":0
}
(HERE/"FORMAL_RESULT.json").write_text(json.dumps(formal,indent=2,sort_keys=True)+"\n")
print(json.dumps(formal,indent=2,sort_keys=True))
