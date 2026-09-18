# Anytime fidelity typed admission R0 — retained result

Issue: #1796 (analytical successor to #1662)
Task: `ANYTIME-FIDELITY-TYPED-ADMISSION-R0-20260919-001`
Frozen base: `c92c985b34a351cbcc12eb6b0d68eb2a14b3c7e3`
Frozen source branch head before formal: `dc21d7033681d38dd1870d83735f3bf0452e3391`

## Decision

`PASS_ANYTIME_FIDELITY_TYPED_ADMISSION_SCOPED`

This is a finite synthetic admission result. It does **not** show that more observation/verification evidence improves a model, that any listed cost matches wall time, or that a production scheduler should use this exact catalog.

## Exact claim

Within the frozen catalog and 385-state model, safe anytime-fidelity admission requires two predicates that a raw scalar "highest fidelity that fits" rule does not encode:

1. the selected variant must cover the evidence roles required by the current semantic decision; and
2. the selected variant's bounded compute cost must leave the explicitly required downstream guard/commit/verification reserve inside the current validity slack.

The frozen `TEMPORAL` and `VERIFY` variants are deliberately same-cost and evidence-incomparable. Therefore a fixed scalar ranking between them is not a safety ordering. A named scalar preset may remain as UI shorthand only when it expands to explicit typed evidence and time-reserve predicates.

## Analytical incomparability proof

Frozen evidence sets:

- `TEMPORAL` covers `{CURRENT, TEMPORAL}` at cost 3 synthetic units.
- `VERIFY` covers `{CURRENT, VERIFY}` at cost 3 synthetic units.

`TEMPORAL` contains the evidence role `TEMPORAL`, which is absent from `VERIFY`; therefore the `TEMPORAL` evidence set is not a subset of the `VERIFY` evidence set.

`VERIFY` contains the evidence role `VERIFY`, which is absent from `TEMPORAL`; therefore the `VERIFY` evidence set is not a subset of the `TEMPORAL` evidence set.

Both have equal bounded cost. Hence neither is uniformly stronger under evidence inclusion, and cost cannot break the tie. Any fixed scalar order between them necessarily prefers one variant in some states where the other is the fitting role-complete choice.

## Formal execution

Source-first discipline:

- local source SHA-256 values were frozen in `FREEZE.json`;
- all five frozen files were published to GitHub before formal execution;
- remote Git blob SHA readback matched local `git hash-object` for 5/5 files;
- ownership reread found only branch `research/anytime-fidelity-typed-admission-1796` and no pre-existing #1796 PR;
- formal invocations: 1;
- reruns: 0;
- post-freeze tuning: 0.

Frozen state space:

- validity slack: 0..10 synthetic units;
- downstream reserve: 0..4 synthetic units;
- every nonempty required-evidence subset of `{CURRENT, TEMPORAL, VERIFY}`;
- total rows: 385/385.

### Comparator outcomes

| policy | unsafe | deadline-reserve violations | evidence-coverage violations | false deferrals |
|---|---:|---:|---:|---:|
| `SCALAR_RAW_HIGHEST` | 224 | 182 | 120 | 0 |
| `SCALAR_RESERVED_HIGHEST` | 120 | 0 | 120 | 0 |
| `SCALAR_RESERVED_POSTCHECK` | 0 | 0 | 0 | 30 |
| `CURRENT_ONLY` | 0 | 0 | 0 | 150 |
| `TYPED_RESERVED` | 0 | 0 | 0 | 0 |

The counts separate two failure mechanisms:

- reserving downstream time removes all 182 deadline-reserve failures from the raw scalar policy;
- it does not repair the 120 evidence-role failures caused by non-nested variants;
- adding a fail-closed postcheck restores safety but creates 30 unnecessary deferrals because it refuses to search an incomparable fitting alternative;
- the typed selector is both safety-clean and feasibility-complete in this authored finite model.

### Selection counts

`TYPED_RESERVED` selected:

- `CURRENT`: 10 rows;
- `TEMPORAL`: 30 rows;
- `VERIFY`: 45 rows;
- `FULL`: 105 rows;
- `DEFER`: 195 rows.

The fixed scalar order never selects `TEMPORAL` when cost 3 is the ceiling because same-cost `VERIFY` is ranked above it. That starvation is a concrete consequence of forcing an evidence partial order into one scalar ranking.

## Independent audit

The auditor re-derived the catalog, feasibility, all five policy decisions, all row metrics, the 385-state set, and aggregate counts without importing candidate policy functions.

Audit result:

- errors: 0;
- typed-row decision mutation detected: yes;
- reported catalog evidence mutation detected: yes;
- aggregate summary mutation detected: yes;
- audit PASS.

Raw rows semantic digest: `4ccae353677ee10825ba187bd4f18e3764e57f20556593f33d5a9222d3fbb919`.
Result summary-core digest: `bf3b78c53494a82162184ffdc1c4fb114456e02024c8b3d4a4ad66d8e3b88904`.

The complete pretty-printed row table is retained as deterministic gzip encoded to ASCII base64 in `ROWS.json.gz.b64`; decode base64, then gunzip to recover `ROWS.json`.

## Design consequence for #1662

Split an anytime-fidelity scheduler into at least two layers:

1. **Safety/admission layer**
   - required evidence roles;
   - source/evidence generation and validity slack;
   - bounded variant compute cost;
   - mandatory downstream reserve;
   - fail-closed DEFER when no variant satisfies both role coverage and reserve.

2. **Utility layer**
   - among safety-admissible variants, choose based on empirically measured task/model utility, token cost, wall time, energy, or other objective.

Do not let the utility layer reinterpret missing evidence as "lower fidelity." Missing `TEMPORAL` evidence and missing `VERIFY` evidence are different semantic deficits, not points on one universal quality axis.

This also separates #1662 from #1663: #1663 can decide whether a computation job is worth running/reusing/rebuilding; #1662 still needs typed admission among alternative outputs of different evidence roles.

## H/T/D/C/U result

**H — PASS within the frozen model.** Raw scalar highest-fit is insufficient due to both reserve and evidence-role failures. Typed reserved admission has unsafe0/false-defer0.

**T — completed.** One source-frozen 385-state exhaustive formal, one independent audit, three corruption controls, no rerun or retuning.

**D — PASS.** Every preregistered discriminator passed.

**C — retained.** A restricted system with truly nested variants, explicit downstream reserve, and empirically monotone utility may safely expose one scalar preset. This result does not rule that out; it rules out assuming those properties from a name like "higher fidelity."

**U — material.** Costs are authored integer bounds; evidence roles are authored; the catalog is small; no stochastic validity process, model quality curve, cache effects, GPU/CPU contention, image encoding, GUI transfer, or production ABI is represented.

## Related disciplines / transfer

- **Real-time systems:** the downstream reserve is analogous to budgeting execution before a deadline rather than treating an upstream stage as the entire critical path.
- **Type systems / information-flow contracts:** evidence roles behave like capabilities or required types; a value with the wrong evidence role is not made valid by being "higher" on an unrelated scalar scale.
- **Operations research / scheduling:** safe feasibility is a constraint problem distinct from utility optimization over the feasible set.
- **Sensor fusion / robotics:** temporal evidence and verification evidence can be orthogonal sensor products even when acquisition costs are similar.

## Stop

Stop this scoped analytical successor after retaining the first PASS. Next evidence, if pursued, should transfer the admission rule to a real bounded observation/verification job and separately measure whether richer admissible variants improve same-model task quality enough to justify their cost.

## ERROR CHECK

- No previous Issue/result was modified or relabeled.
- No shared runtime/workflow/history path was changed.
- Exhaustive formal executed once only.
- Remote frozen-source blob identity was checked before formal.
- Auditor did not import candidate policy functions.
- PASS scope is explicitly finite/synthetic and does not claim production utility.
