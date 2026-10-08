# Role-skill lifecycle amortization (-04)

New construction allocation under Issue #5133 after the immutable -03
construction STOP. -03 failed because a Windows host path was checked from
inside the Linux container. This -04 test separates host filesystem checks
from Linux mount-mapping checks. The -01/-02/-03 evidence and freezes remain
unchanged; this is not a retry of a container invocation.

## H / T / D / C / U

**H — hypothesis.** For the exact retained seed-3788 synthetic role-skill
package, loading, parsing, digest/schema/shape validation and constructing the
selected role for every request costs more over 1,000 requests than one
complete load/validation/all-role construction followed by reuse, while
producing identical predictions.

**T — treatment.** Fifteen paired blocks in alternating AB/BA order. Each arm
handles the same deterministic 1,000-row A/B/C schedule in every block (30,000
predictions per arm). `RELOAD_EACH_REQUEST` includes full load, validation,
selected-role construction and scoring per request. `LOAD_ONCE_REUSE` includes
full package validation and construction of all roles in initialization cost,
then scores with reused role models. Process startup is excluded equally.

**D — decision.** `PASS_LIFECYCLE_AMORTIZATION_SCOPED` requires exact frozen
source/reference/input/image identity; construction parity on all 12,288
retained predictions; formal prediction reconciliation on 30,000/30,000 rows
against the retained oracle; a clean independent raw-only audit rejecting all
seven mutation controls; reuse wins at least 12/15 paired blocks; median
lifetime ratio at most 0.90; and median first cumulative break-even request at
most 1,000 (non-crossing blocks are censored at 1,001). Identity/audit defects
are STOP, semantic disagreement is FAIL, and a valid unmet performance gate is
HOLD. No retries, replacement runs or pooling.

**C — controls.** Same package, scorer, frozen input schedule, process boundary,
CPU-only runtime, image and CPU limit; lifecycle is the intended difference.
Reuse initialization is included. The runner and auditor are separate
invocations. The auditor reconstructs predictions without importing the
candidate. Network is disabled; root and source mounts are read-only; only the
dedicated output directory is writable. No package installation.

**U — uncertainty.** One synthetic package/seed and pure-Python scorer. This is
not a model fit, PyTorch/framework speed result, real-time fine-tuning result,
LoRA efficacy result, role-network/skill task-success result, GUI effect,
production latency or product claim. It does not close #4916.

## Frozen procedure

`FREEZE.json` is the authority for source and reference hashes, image identity,
container limits, exact host paths, and the three commands. The only valid image
is the locally cached `python:3.13.5-slim-bookworm` with the recorded ID. Do not
pull or build an image. Run construction once; only on a passing receipt run
formal once; only after formal exits zero run the independent auditor once.
Preserve all stdout/stderr and output files verbatim. A failed preflight means
STOP before a container is started. A launched invocation is never retried.

Local host tests can be run with `python -B -m unittest discover -s
research/analysis/needle_role_skill_lifecycle_5133_v2 -p test_lifecycle.py -v`.
They are construction checks only and do not authorize or count as a container
run. A named serialized Docker CPU slot for this exact allocation is required
before any construction, formal, or audit container invocation.
