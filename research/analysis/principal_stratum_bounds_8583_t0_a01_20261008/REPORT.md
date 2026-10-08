# Issue #8583 T0 A01 — formal result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate and the separately implemented independent auditor each ran exactly once in WSLc; both exited 0. The auditor reconstructed all compatible tables in all four cases with zero discrepancies and rejected all five preregistered candidate mutations. No retries.

## Result

| Fixture | Compatible latent tables | p0 observed contrast | p0 always-demand contrast | Interpretation |
|---|---:|---:|---:|---|
| `asymmetric_selection` | 5 | −1/3 | [−1, +1] | bounded, not point identified; an opposite-sign compatible completion exists |
| `equal_demand_point` | 1 | +1 | [+1, +1] | point identified in this fixture |
| `empty_always_compatible` | 2 | +1 | [+1, +1] over nonempty completions | `UNIDENTIFIED_EMPTY_STRATUM`: another compatible table has no always-demand units |
| `no_p0_demand` | 1 | null | null | no p0 demand and no always-demand units; outcome/contrast remains undefined |

Across all policies, the auditor verified exact rational margins, compatible-table sets, identification labels, bounds, empty-stratum flags, and undefined cells. No cross-world assumptions were used. A numerical bound over nonempty compatible strata is not presented as identification when an empty-stratum completion is also possible.

## Execution record

- Freeze commit: `01977cacd147419b86fcc59eef3e17cb19e83252`; branch base: `28b6f0fc0dd3cf6d798d97ee608a409ce773e409`.
- Runtime: Microsoft WSLc 3.0.1.0; local `python:3.12-slim`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; Python 3.12.14; linux/amd64. No Docker Desktop.
- Frozen command: `wslc run --rm --mount "type=bind,source=<checkout>/research/analysis/principal_stratum_bounds_8583_t0_a01_20261008,target=/experiment" --workdir /experiment python:3.12-slim python -c "import subprocess,sys; p=subprocess.run([sys.executable,'candidate.py']); sys.exit(p.returncode) if p.returncode else None; a=subprocess.run([sys.executable,'auditor.py']); sys.exit(a.returncode)"`.
- Candidate: exit 0; output `results/candidate_raw.json` (3,817 bytes).
- Independent auditor: exit 0; output `results/audit.json` (532 bytes), `PASS_METHOD_SCOPED`, four cases reconstructed, 0 errors, 5/5 mutations rejected.
- Construction suite before freeze: 2 tests passed under normal Python and 2 under `python -O`. A deliberately invalid hostile-input test edit initially targeted a still-valid margin; correcting the test to target zero-demand/positive-success produced green results in both modes. Construction checks are separate from the one-shot formal run.
- Before the freeze commit, Git refused staging because the new path was outside the worktree sparse definition. The exact path was added to this worktree's sparse definition and staging/commit then succeeded. This was an administrative pre-run issue, not a candidate/auditor execution or scientific STOP.

## Scope and limitations

This is a finite synthetic exhaustive-enumeration result for four authored margin tables with population sizes 2–3. It has no sampling uncertainty and is not an empirical causal estimate, general theorem, real policy/recovery effect, model/GUI/application result, or product claim. No monotonicity, exclusion, or other cross-world assumptions are invoked. WSLc is the experiment runtime; no claim is made that CPU/memory limits are enforced by the host.

The original issue and predecessor outcomes are unchanged. This additive successor only answers the frozen finite compatibility question. Raw evidence and source/input identities are retained alongside this report.
