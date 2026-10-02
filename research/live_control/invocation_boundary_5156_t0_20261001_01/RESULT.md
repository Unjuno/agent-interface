# #5156 T0 invocation-boundary result

## H / T / D / C / U

**H.** A run-specific invocation ID and per-invocation artifact namespace can
distinguish attempts within one allocation. Legacy evidence without that ID
must remain unbound; the system must not infer an exact historical run count.

**T.** Freeze eight synthetic cases and four immutable Allocation 04 Git blob
references. Run one candidate classification and, only after candidate exit
0, one separately implemented raw-only audit. No retry.

**D. `STOP_INVOCATION_BOUNDARY_AUDIT`.** The candidate exited 0 and emitted
8/8 case rows. The independent auditor exited 1: it reconstructed the raw
rows without a candidate mismatch, but reported only 5/6 mutation/negative
controls rejected. Read-only inspection found the first “mutation” was a
no-op: it rewrote the positive row's `decision` to the value already present.
Thus the auditor's declared mutation coverage is incomplete, and the frozen
gate is not met. This is a validation-harness STOP, not a PASS for the full
contract and not evidence that the candidate's classification is incorrect.

Important bounded observation: for the historical Allocation 04 fixture,
the candidate emitted `invocation_count: null` and
`STOP_INVOCATION_PROVENANCE_OR_BOUNDARY`, without assigning IDs or claiming
that the three listed artifacts prove three distinct invocations. The two
uniquely tagged attempts in a separate synthetic case were counted as 2 and
correctly exceeded the one-invocation limit. These are candidate outputs only;
the audit STOP prevents promotion to a verified result.

**C.** CPython 3.12.10 on Windows; host-only standard-library data. No
Docker/OrbStack, X11, XTest, GUI, input, model, GPU, or network. The #5085
shared container slot was not assigned to this work. The historical STOP/raw
artifacts were referenced by Git blob and read only.

**U.** No conclusion about the #5156 key-up hypothesis, actual X11 execution,
allocation one-shot compliance, physical held-input occupancy, MAP01, task
effect, or safety. This T0 does not repair or re-label Allocation 04. Its
candidate and auditor invocations are consumed under the frozen no-retry
rule; a corrected audit requires a distinct successor, not a rerun here.

## Execution record

- Pre-freeze construction tests: `python -m unittest -v test_boundary.py` —
  7/7 passed.
- Pre-freeze compile: `python -m py_compile runner.py audit.py test_boundary.py`
  — passed.
- Candidate: one invocation; exit 0; 8 rows; raw SHA-256
  `d3fb121b95d95fa61ea771a7dd0c20a8e255ea83b72752a3ebe371b27762d4b2`.
- Independent auditor: one invocation; exit 1;
  `STOP_INVOCATION_BOUNDARY_AUDIT`; audit SHA-256
  `7ade1dcddb23cb9249f57e27e1e14c0f2ba1bc27a585c6b19231af986dba4331`.
- No candidate/auditor retry was made. The no-op mutation was found by
  read-only source/output inspection after the audit.

Exact preregistration and source/reference hashes are in `FREEZE.json`.
Candidate output is `results/raw.jsonl`; the independent auditor receipt is
`results/AUDIT.json`.
