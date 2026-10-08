# #5274 — typed evidence frontier and explicit decision finalization

**PASS_TYPED_REDUCER_FINITE_SCOPED.** One prospective, source-frozen finite
allocation; no formal retry, source tuning, replacement, or excluded formal row.
This is research evidence, not a production runtime or Verification Orchestra
integration. Broad #5274, #5267 and ROADMAP remain open.

## Results

| Measured finite object | Count / result |
|---|---:|
| Distinct evidence sets | 365 |
| Distinct arrival permutations | 1,644 |
| Prefix verdicts independently reconstructed | 4,699 |
| Post-finalization arrivals | 3,288 |
| Independent oracle disagreements | 0 |
| Final PASS / FAIL / UNCERTAIN outputs | 71 / 482 / 1,091 |
| Candidate unit methods | 14 passed |
| Effective copied-evidence corruptions rejected | 12 / 12 |
| Formal orchestration / retries | 1 / 0 |

The three verdict counts are intended fixture outcomes, NOT an accuracy of
71/1,644. All 1,644 cases agree with the separately implemented contract oracle.
343 three-check combinations cover missing, PASS, FAIL, UNKNOWN, TIMEOUT,
historical PASS and predicted PASS. Another 22 sets cover conflicts, duplicate
identity, exact retransmission, malformed types, wrong bindings and roles.
All distinct arrival permutations are included. These are finite model cases
in one real JSONL subprocess, not 1,644 independent OS or application trials.

## Interpretation / examples

Evidence accumulation, not the provisional three-label verdict, is monotone.
A later current conflicting result can correctly revise provisional PASS to
UNCERTAIN. Explicit finalization freezes one evidence frontier; this is an
immutable decision record, not proof that every real-world verifier finished.
Late evidence must be retained by a future orchestration layer and trigger an
explicit new review when needed; this prototype grants no action authority.

Two mandatory checks use distinct roles: A requires CURRENT target evidence;
B requires VERIFIED_EFFECT result evidence. C is optional diagnostics. Optional
PASS cannot hide an unopposed mandatory FAIL. Missing mandatory current evidence
cannot be supplied by historical or predicted PASS. Same-check PASS plus FAIL
is CONFLICT. A required check with FAIL and UNKNOWN/TIMEOUT but no PASS is FAIL.
An independently unopposed required FAIL dominates unrelated uncertainty or
malformation. Otherwise all mandatory PASS with no integrity faults is PASS;
remaining cases are UNCERTAIN. Optional conflicts remain visible but do not
veto the explicitly required contract. See the exact precedence and full
conditional proof/variable table in [PREREGISTRATION.md](PREREGISTRATION.md).

Global evidence IDs are a declared assumption, not a universal producer rule.
The parallel vj01 producer-local ID namespacing allocation is separate. The
pre-run coordination reread found its explicit deferral of the general matrix
(comment 5891528179); none of its code, sources or formal cases were touched.

## H / T / D / C / U

H: union-only evidence and a frozen finalization cut give set-order invariance,
while required failures, missing checks, conflicts and quarantined evidence
retain their different meanings.
T: fixed 365-set/1,644-ordering JSONL corpus through an exec'd Python reducer.
The independently structured raw auditor imports no candidate/runner/generator.
D: complete corpus and source identities; all prefix/final/late states match;
zero authority; exact retransmission; normal process exit; full LF framing;
all 12 effective corruption controls reject. All gates passed.
C: ordering invariance of a set function is established conditional on the
fixed rule. It does not prove that the rule is right for arbitrary applications.
U: trusted test source mapping; CURRENT is a typed fixture role, not measured
capture freshness. No authentication, verifier truth, required-set completeness,
real dependency/IR integration, model/GUI/task success, latency/token benefit,
production capability or cross-platform claim. Independent audit means another
implementation/process, not another person. Numeric u_c/coverage k are not
estimated; no physical performance inference is made.

## Execution and retained failures

Provided Linux 6.18.44 x86_64/glibc 2.41 container, CPython 3.13.5; standard
library only. Exact environment/interpreter hash is in the restored evidence.
Docker CLI/image identity was unavailable: not Docker/OrbStack replication.
No package installation, credentials, model/provider, GUI/input, or external
network requests were part of the experiment.

Source commit `9190473c5cbf31d76050a3ab81e5997bfa43a0a9` and preformal Issue
comment 5891541067 preceded the sole formal command. Intake main was
`4244aaf8b1d0ad2b26d64813842f801ce8f66612`. Frozen source pack was published
and its Git blob read back before execution. It contains all six exact Python
sources, preregistration, environment, source manifest and construction evidence.

Actual formal command was `PYTHONDONTWRITEBYTECODE=1 python -B run.py formal-01`.
The added -B agrees with PYTHONDONTWRITEBYTECODE; it changes no science.
One child with a 20-second deadline exited 0; driver exit 0; both stderr empty.
No latency criterion is inferred from run chronology.

Two preformal construction mistakes are retained: first invocation omitted
--construction and stopped at missing FREEZE before any child; later a control
harness used dict equality and falsely treated integer 0 to Boolean false as
an ineffective change. Auditor rejection already worked. Canonical typed-byte
comparison corrected only control accounting before source freeze. The six
construction cases and their failed reports are excluded from formal counts.

## Reconstruct and independently audit (no formal rerun)

Python 3.13; no third-party packages. From this repository directory:

```sh
python restore.py /tmp/reducer5274-review-new
cd /tmp/reducer5274-review-new
python -B audit.py formal-01 REVIEW_AUDIT.json
python -B controls.py formal-01 REVIEW_CONTROLS.json
python -B tests.py
```

Use a new destination: restore refuses overwrites. It verifies all six binary
parts, the complete archive hash, 44 regular members and all 43 manifest entries
before extraction. It runs no study. The consumed formal-01 directory remains
present; do not remove it or rerun the scientific allocation.

Two separate read-only revalidations completed: a fresh copied study directory
reproduced audit/controls byte-for-byte and 14 unit tests; then reconstruction
from these exact binary parts reproduced AUDIT.json byte-for-byte. Packaging
checks reject an existing destination and a changed part before extraction.

Archive: 68,036 bytes / 44 files; SHA256
`7fb949e3fe109494377d1b108212876c4b4d5d703f13758bfb59d3a999b99016`.
Requests SHA256 `1dba2f07b352f6909d2ab84c3400d6f4c32a3120f2071b8b91f320bb608da61b`.
Responses SHA256 `026e4d169484bb2f300882249b7e6b53fec076099c2d363fc671a0cb0b78b7aa`.

## Integration boundary and next smallest step

Deliver only this additive research namespace. No shared runtime, global goal,
workflow, previous allocation or foreign branch is changed. Repository-wide
runtime tests were not executed locally; PR CI/review is a separate gate.
For integration, consume the scoped reducer rule only after binding an actual
required-check registry and producer contract to the existing IR. Do not infer
permission to execute from a sealed historical PASS. The next concrete question
is how completion receipts define the cut and how relevant post-cut evidence
causes an explicit new revision. Existing producer-ID work remains separate.
