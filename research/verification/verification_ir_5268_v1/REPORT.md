# Issue #5268 — finite Verification IR v0.1 result

## Intake and selection

- Repository: `Unjuno/agent-interface`; current `main` at intake:
  `6cd858858f0909cab5357de054404792a0148910` (2026-09-29), also confirmed by
  the GitHub MCP commit endpoint.
- The root README frames the work as research preview: preserve rich-model
  intent, use bounded local mechanisms, and let fresh evidence govern authority.
- `docs/CURRENT_GOAL.md` is r133: posthoc SHA-bound reconstruction of retained
  v38/v39 MAP01 traces, with no new model/GUI calls; its next measurements are
  held-input occupancy, independent useful feedback, bounded recovery, and
  transfer coverage.
- Root `ROADMAP.md` still labels 2026-09-19 desktop integration as current
  priority and leaves the larger interaction/runtime/release checklist open.
  Its checkboxes show 6 checked and 36 unchecked. This is older than r133; the
  two documents are not silently reconciled here.
- Open Issue/PR and branch inventories were checked through GitHub MCP. #5268,
  #5269 and #5275 were open and had no associated PR/branch/comment at intake.
  #5274 already has merged PR #5283 and is not duplicated. #5269/#5275 depend
  on a frozen IR, so #5268 is the appropriate foundational finite experiment.
- Closed #4157 remains `PASS_DEADLINE_VALIDITY_SCOPED` (24/24) for its separate
  deadline contract. Live #17 covers the safety plane. The current #701 issue
  is titled as an applicability-envelope review, despite #5268/#5269 citing
  that number as typed evidence/applicability-role work. This mismatch is
  recorded, not relied on or edited.
- Parallel #5134 formal MAP01 work was explicitly excluded; its shared
  one-shot output, branch, and queue were not touched.

## H / T / D / C / U

**H.** A deliberately small typed IR can preserve the required checks for a
frozen 10-case Agent Action corpus: primitive, subject, criticality, required
evidence role, verifier class, dependency, deadline slot, budget class, and
fallback. It carries no authority and makes unknown requirements explicit.

**T.** Freeze 10 hand-authored cases and a separately authored literal oracle.
Lower each case, JSON-round-trip it, compare all fields with a raw-only auditor,
then mutate retained plans with eight correctness corruptions. No model, task
input, GUI, or external service is called. The formal runner refuses overwrite.

**D.** `PASS_IR_ORACLE_FINITE_SCOPED` iff all 10 plans exactly match, no
authority field is emitted, the unknown marker remains explicit, and all eight
corruption controls are rejected. Result: **PASS_IR_ORACLE_FINITE_SCOPED**.

**C.** A small hand-curated corpus and oracle may share omissions or favorable
assumptions; agreement could reflect fixture construction rather than coverage
of real Agent Actions. The candidate may simply restate existing contracts.

**U.** This is synthetic finite coverage only. It does not show a complete
ontology, real verifier correctness, authority/currentness truth, learned
routing quality, safety improvement, runtime integration, latency/token/task
benefit, or cross-domain transfer. The independent auditor is a separate code
path but not a second human. No elapsed-time metric is claimed.

## Frozen method and execution

Allocation `verification-ir-5268-v01-20260930-01` was frozen at source commit
`6cd858858f0909cab5357de054404792a0148910`. The study ran once in
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
Linux/arm64, CPython 3.12.14. Container had no network, one CPU, 512 MiB,
128-PID cap and read-only root (only the isolated study bind mount was writable).
Exact source hashes and command are in [FREEZE.json](FREEZE.json).

Formal command executed once:

```sh
docker --context orbstack run --rm --name unjuno-5268-ir-formal-01-20260930 \
  --network none --cpus=1 --memory=512m --pids-limit=128 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  -v <study_dir>:/work:rw -w /work \
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -I -S -B -c 'import sys,runpy; sys.path.insert(0,"/work"); runpy.run_path("/work/run_formal.py",run_name="__main__")'
```

It exited 0 and retained 10 raw action/IR records. A separate container ran
`audit.py --out AUDIT-01.json` read-only with respect to source/result; it
exited 0 and independently reconstructed 32 checks with zero disagreement.
The auditor imports neither `candidate.py` nor `run_formal.py`.

Execution note: `PLAN.md` shows the auditor's stdout mode; the actual invocation
used `--out AUDIT-01.json` to retain the audit summary as an artifact. This
changed only where the audit summary was written; the formal input/output and
audit gates were unchanged.

The raw outputs hash to:

```text
FORMAL-01.json  a1c9f38ffeea5a8bbd700fa59a1482330bf685d4b8e696f1199e95d53e053b30
AUDIT-01.json   69f58215265f4be9ad15acc764b1351494a09406e6ba3b5873dbeb41a674ca72
FREEZE.json     38869a5d908799c6a6bfeb0f2a68a3e627c3b0f9b6c9389168b58de378aa2318
```

Construction tests passed **7/7** before the formal freeze/run. TDD construction
failures are retained in this report and are not counted as formal outcomes:
the first isolated invocation used unittest's module loader, which could not
find the script under Python isolated mode; the corrected `runpy` invocation
then failed because the candidate module did not yet exist (expected RED).
The independent-auditor test similarly failed before `audit.py` existed. A
malformed list-valued primitive initially raised an uncontrolled `TypeError`;
the test exposed it, and the candidate was changed to reject it as a controlled
`ValueError` before freeze. The final container test run was clean.

## Interpretation and next integration boundary

The IR retains `MANDATORY`, `CONDITIONAL_MANDATORY` and `OPTIONAL` distinctions;
the raw set contains 30 mandatory, one conditional-mandatory and one optional
check. Exact roles keep current observation, intent, permission, clock,
action-contract, verified-effect, unknown-requirement and diagnostic coverage
separate. Adding an `authority` key, unknown primitive, or hiding an unsupported
requirement is rejected by the schema/oracle gates.

This is a useful first boundary for #5268, not yet evidence that the namespace
is ready for #5269 mandatory coverage or #5275 OOD detection. Before those
successors, review whether the v0.1 primitive/role set is genuinely grounded in
the contracts and correct the #701 reference if needed. Do not use this result
as an action-admission gate; it emits no action verdict or authority.
