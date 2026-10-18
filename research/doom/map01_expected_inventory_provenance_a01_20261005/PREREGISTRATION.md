# Expected-key inventory provenance construction A01

## H / T / D / C / U

**H:** The completeness wrapper from the per-key ledger construction accepts a partial telemetry ledger as `BOUNDED` when its caller supplies an expected-key inventory that has been understated to match the observed rows. This would show that row-completeness checking is conditional on inventory provenance.

**T:** Pin the exact candidate wrapper, legacy ledger, and two-key retained fixture from PR #7695. Evaluate four cases: complete ledger with the correct inventory; omitted `SPACE` with the correct inventory; omitted `SPACE` with caller inventory `W`; complete ledger with caller inventory `W`. Run a separate raw-only auditor that independently reconstructs row identities and interval bounds and checks the candidate output. No game, input, X server, model, or shared compute resource.

**D:** `PASS_INVENTORY_PROVENANCE_COUNTEREXAMPLE` iff the two correctly configured controls behave as expected (complete/correct is `BOUNDED`; omitted/correct is `UNKNOWN`), omitted/underdeclared inventory becomes `BOUNDED`, complete/underdeclared remains `UNKNOWN`, and raw-only audit confirms the mutated set contains only `W` while the original fixture contains `SPACE` and `W`. Any mismatch is `FAIL`; incomplete artifacts are `HOLD`.

**C:** The fixture is a deterministic retained synthetic event set. The audit verifies what the wrapper does with a supplied inventory; it cannot authenticate an action's expected keys because the retained fixture has no separate admission record.

**U:** This tests one composition boundary only. It does not establish live occupancy, physical release timing, game behavior, useful feedback, recovery, task effect, MAP01 progress, or general runtime safety. A confirmed counterexample means any future completeness claim must bind the expected set to independently retained action-admission evidence.

## Frozen source

- Candidate package head: `7ed0dd27c3ebde976744cc7cae0062d8b449eb14` (PR #7695).
- Current repository main at experiment selection: `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Candidate, legacy ledger, raw fixture, protocol, runner, and auditor hashes are recorded in `FREEZE.json` before execution.
