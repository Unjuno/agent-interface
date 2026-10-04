# Visible Undo history versus real compensation footprint

SUPPORT_VISIBLE_HISTORY_INSUFFICIENT_SCOPED / HOLD_MODEL_POLICY_AND_SAFE_COMPENSATION.
Two NEW disposable real LibreOffice25.2.3.2 headless Calc documents, actual
XUndoManager and ordinary setString recording; no simulated undo objects.
Immediately before one Undo, both documents have A1=OWNED, B1=PROTECTED,
titles=[Input], undo_possible=true, locked=false. In single_visible, B1 was
set while recording was explicitly locked, then A1 recorded normally. Undo
clears A1 and preserves B1. In hidden_attached, A1 records normally, then
enterHiddenUndoContext attaches recorded B1; Undo clears A1 AND B1.

Saved FODS hashes and independently reopened read-only cells confirm both
post-Undo effects. Producer/LibreOffice parent exit0. Same-author supplemental
read-only reopen auditor exit0/errors[] and both imported docs ReadOnly=true;
source/data/FODS hashes checked before and after. No original Undo or producer
replay. This is a distinct saved-document audit, not a rerun of the first audit.

The original R02 XML auditor FAIL_OR_HOLD/exit1 is retained: it expected two
explicit table cells, but the fully blank saved sheet has one empty cell.
No change or regrading of that auditor/result. Original R01 remains HOLD:
.uno:EnterString did not modify A1 in this headless route, while setString did
create an Input record. R02 uses fresh docs and a separately frozen corrected
operation/setup; it does not reuse a consumed formal allocation. R01 raw's
OBSERVED label is not qualification of its intended contrast.

First base-image eligibility found no UNO Python binding. First BuildKit launch
could not resolve the local sha256 FROM; all original build/source/stdout/stderr
retained. Separate public Debian trixie-slim build produced immutable image
sha256:ded219f2bc3b57fd6e452cd9ccae7cb35e3bcfc24ea140f381ad4d2b1976b8dc,
with actual LibreOffice25.2.3.2 and python3-uno. Build used package networking;
experiment/audits network-none, nonroot, CPU1/memory512M requested. Effective
cgroups not sampled for these runs; swap-limit warnings retained.

B1 protection/attribution is authored: no independent concurrent writer or
authenticated ownership demonstrated. Baseline recording lock is not semantic
mutation exclusion. Different recording histories are intentional: identical
current cells and visible titles cannot identify their different footprints.
No model policy, native keyboard/mouse, task usefulness, speed, crash atomicity,
general compensation or authority/release certificate. No custom undo action or
selective-undo subsystem. A safe generic compensation policy remains HOLD;
prefer current-state recheck/SAVE_AS_NEW/ABORT where attribution is unavailable.
Closed421 unchanged. Stop additional API variations as a substitute for the
remaining same-model held-out operation, conflict and protected-effect gates.

Issue comment5974510416 prematurely claimed first auditPASS; correction5974512331
withdraws it. Both records remain immutable; supplemental audit is separate.
