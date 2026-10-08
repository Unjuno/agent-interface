# T0 A01 preregistration — Issue #8586

## Research question

Does an explicit task-conditioned degraded-configuration envelope prevent a
joint capability loss from inheriting permission by composing individually
qualified fallback edges, while retaining every continuation supported by the
frozen task contract?

## H / T / D / C / U

**H.** In the frozen finite task/capability model, the edge-by-edge fallback
baseline will permit at least one unsupported joint-loss continuation for the
two-view sibling-preservation task. The task-conditioned envelope will refuse
that route, retain every feasible route, and preserve all hard gates. The
blanket-stop baseline will refuse at least one feasible single-loss route.

**T.** Exhaustively enumerate three task classes, all subsets of six named
capabilities, and six context states: 3 × 2^6 × 6 = 1,152 rows. Compare the
edge-by-edge fallback composition, stop-on-any-loss, and TDCE route selection.
An independently implemented raw-only auditor reconstructs the grid,
obligation coverage, route support, decisions, hard-gate fields, and the
preregistered comparisons. Construction tests also mutate the joint-loss
decision, hide an obligation or hard gate, forge compensator availability,
reuse an expired allowance, remove a row, and convert UNKNOWN to continuation.
No model, GUI, OS input, user data, external effect, or container is needed.

**D.** `PASS_METHOD_SCOPED` only if the independent audit reconstructs all
1,152 rows, reports zero TDCE/oracle mismatches and zero TDCE false continues
or false stops, finds at least one joint-loss false continuation in the
edge-wise baseline, finds at least one feasible case rejected by blanket stop,
and all frozen mutation controls are rejected. Otherwise preserve the first
`FAIL_METHOD` or `HOLD` outcome. This is a finite authored-model result only.

**C.** A qualified capability graph may already encode joint dependencies;
the capability-loss matrix may omit real interactions; and a small explicit
route table may cost more to maintain than it saves. A conservative blanket
stop may be preferable for tasks where no degraded route is independently
qualified.

**U.** The tasks, route proofs, context states, and capability failures are
authored. No result establishes that these failures occur in production, that
the model is calibrated to a live GUI, or that a TDCE improves runtime safety,
reliability, latency, or product behavior. The candidate does not change
runtime code or authority.

## Frozen finite model

The immutable `model.json` defines three task contracts, their route capability
sets and proved obligations, six capability bits, universal/task-specific hard
gates, and six context modifiers. The auditor has a separately written oracle
table for task obligations and route proof claims; it does not import the
candidate. Joint loss of `semantic_target` and `native_effect_check` on
`preserve_sibling_edit` is the planned non-additive case: the edge baseline can
combine `pixel_target` and `visual_diff`, but that combination does not prove
`sibling_unchanged`.

Both formal CLIs verify the exact frozen source hashes before use. The candidate
raw binds the allocation, base commit, freeze digest, model digest and candidate
digest; the auditor independently verifies those values and records its own
source digest.

Every row retains all hard gates; their presence in the synthetic record does
not mean the candidate executes or satisfies those gates in a real system.
`compensator_missing` is not applicable to `read_one_value`; an expired
degraded allowance blocks only when the task's primary route is unavailable.

## Execution and stop rule

Freeze `FREEZE.json` and verify the listed hashes before formal execution.
Invoke the candidate once. Invoke the auditor once only if the candidate exits
0 and its raw output exists and is nonempty. Do not retry either invocation.
If candidate or auditor launch/output fails, retain the exact failure as HOLD or
STOP; do not change code or reinterpret the frozen allocation. Construction
tests may run before freeze and are not formal rows.

```sh
python3 -B -m unittest -v test_construction.py
python3 -O -B -m unittest -v test_construction.py
python3 -B candidate.py model.json results/candidate.raw.json
python3 -B auditor.py model.json results/candidate.raw.json results/audit.json
```

The first two commands are construction checks. The final two are the single
formal candidate/auditor invocations and are run only after freeze. There is no
formal rerun path in A01.
