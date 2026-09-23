# P0 current causal-trace source closure
TASK: P0-PHYSICAL-USEFUL-TRACE-CURRENT-CLOSURE-20260918-002
BASE: 51d9f5b3b534286f9a4ac50e6a2321e919300a0d

H: Current retained evidence closes semantic + offline implementation mechanics through v12, but does not close live physical-edge transfer or a live independently scored useful-effect sample.
T: Source-bound facts only; deterministic evidence-class DAG; same-process and cross-process clock variants; one primary invocation; no X11/model/input.
D: PASS_P0_CURRENT_GAP_LOCALIZED_SCOPED iff offline_ready=true, live useful control=false, live physical/effect gates remain unproven, cross-process clock claim is not treated as proof, queued #1099 contributes zero reachability.
C: A private-X11 transfer can fail despite offline correctness. Cross-process effect timestamps need a measured clock relation; same-process can avoid that extra dependency only if process/clock identity is retained in the live evidence itself.
U: Source closure only; no physical truth, effect causality, MAP01 usefulness, or production claim.
