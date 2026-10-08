# Issue #5442 T3 — derive receipt observer fault domains

## Provenance and boundary

Fresh T3 successor to the open Issue #5442 chain. T2 explicitly identified
shared observer dependencies as unresolved and asked for dependency provenance,
common-cause partitions, and an abstention or trusted-endpoint comparison. No
same-number active branch or PR was found in the bounded GitHub search on
2026-10-01. T3 is a deterministic host-local finite semantic simulation; the
shared OrbStack lane remains subject to the unresolved cross-context
provenance hold in #5085. No Docker/OrbStack command is issued.

## H / T / D / C / U

**H:** Two fresh receipts that agree on the intended post-state can still
false-confirm if their derived provenance closures share a faulting component.
A gate that derives fault domains from a receipt dependency DAG and excludes
observers touched by a declared failed dependency will prevent that common-mode
false commit. It may abstain when only correlated observers remain. An
explicitly trusted actuator-side observer can resolve a receipt only under the
stipulated trust assumption.

**T:** Freeze five scenarios on one provenance DAG: no fault; parser-A fault;
parser-B fault; shared-cache fault that makes A/B jointly report the intended
state although ground truth contradicts it; and actuator-readback fault while
A/B remain correct. Compare (1) T2-style A/B agreement, (2) provenance-derived
independent-pair admission with abstention, and (3) the same gate with an
explicitly trusted actuator-side C observer. The simulator emits the graph,
fault set, ground truth, observer reports, and policy summaries once. A separate
raw-only auditor derives each observer's faultable dependency closure from graph
edges and recomputes all policies. Six graph/receipt/summary corruption
controls are required.

**D:** `PASS_DEPENDENCY_CUT_METHOD_SCOPED` iff A/B agreement false-confirms the
shared-cache counterexample; both provenance policies refuse that false commit;
the independent-pair policy preserves confirmation for no-fault and
single-parser-fault cases; it abstains when a shared fault invalidates A/B or
when only correlated A/B remain; trusted C reports the stipulated actual
contradiction under the shared-cache fault; raw-only audit has zero errors; and
all six mutation controls are detected. Any policy commit on the stipulated
false-goal row is FAIL.

**C:** A less conservative policy may use calibrated failure probabilities,
redundant endpoint attestations, or action-specific loss budgets. This model
does not estimate which observer is most trustworthy and does not justify
relying on C in a real system.

**U:** Dependency DAG, failure declarations, observer outputs, and C's trusted
status are hand-authored. The test does not validate provenance extraction,
failure detection, observer independence in software/hardware, adversarial
forgery, timing, latency, real task effects, or production safety. It is a
finite mechanism probe only.

## Frozen commands and execution boundary

- Base: `51dd32406fe64c10eb8c2408ffc4682f0939dc41`.
- Host: CPython 3.14.5, standard library; no network, GUI, model, container, or
  external effect.
- Construction tests:
  `python3 -B -m unittest discover -s research/analysis/semantic_receipt_dependency_cuts_5442_t3 -p 'test_*.py' -v`
- Candidate (one invocation):
  `python3 -B research/analysis/semantic_receipt_dependency_cuts_5442_t3/candidate.py > research/analysis/semantic_receipt_dependency_cuts_5442_t3/raw/candidate.jsonl`
- Independent audit (one invocation, only after candidate exit 0):
  `python3 -B research/analysis/semantic_receipt_dependency_cuts_5442_t3/audit.py research/analysis/semantic_receipt_dependency_cuts_5442_t3/raw/candidate.jsonl > research/analysis/semantic_receipt_dependency_cuts_5442_t3/raw/audit.json`
- Corruption controls (one invocation):
  `python3 -B research/analysis/semantic_receipt_dependency_cuts_5442_t3/corruption_controls.py research/analysis/semantic_receipt_dependency_cuts_5442_t3/raw/candidate.jsonl > research/analysis/semantic_receipt_dependency_cuts_5442_t3/raw/corruption-controls.json`

Source hashes are frozen in `FREEZE.json` before candidate CLI execution. No
candidate rerun, tuning, or replacement.
