# Issue #5269 — deterministic mandatory-plan coverage

## Result

**`HOLD_UNREPRESENTED_RISK_ESCALATION`**. The finite coverage boundary behaved as expected on the frozen #5268 corpus, but the #5269 decision gate is not fully met: Verification IR v0.1 has no risk-escalation primitive or tier field, and the external-side-effect fixture is only a high-consequence proxy. No escalation rule was invented after seeing the outcome. Keep #5269 open and coordinate its missing policy boundary with #5266/#5273 before claiming full success.

This is not a runtime admission change, action permit, evidence-truth result, or router-quality result.

## Frozen design and run

See [PLAN.md](PLAN.md) for intake, branch/PR collision review and H/T/D/C/U. Source and parent input identities are in [FREEZE.json](FREEZE.json). The run used the pinned Python 3.12.14 Linux/arm64 image, one CPU, 512 MiB, no network, read-only root, and a single writable output mount. Formal was invoked once; no model, task input, GUI, OS input, verifier execution, or external service was used.

The required rows from all 10 #5268 cases matched its independent literal oracle. Coverage accepted 12 valid plans (10 complete plans, optional diagnostic omitted, optional diagnostic added), and rejected 39 proposals. That is 51 attempts total. Each of the 31 non-OPTIONAL rows received its own omission control; each was rejected. Named corruption controls for downgrade, wrong target/subject, evidence role, intent generation, infeasible supplied verifier bound, unknown primitive, duplicate/conflicting row, and external-side-effect safeguards were also rejected. A separate auditor recomputed 12 accepts/39 rejects with zero attempt-decision disagreement.

The deadline test used an explicit synthetic `upper_bound_ms=11` against a deadline of `10`. It demonstrates comparison logic only; it is not a measured verifier SLA or #5273 registry. The external-side-effect case verifies action-dependent `EFFECT.REVERSIBILITY` and `EFFECT.POSTCONDITION` coverage; it does not establish a general risk-tier or escalation policy.

## Preserved audit and construction incidents

- `AUDIT-01.json` is retained unchanged. Its independent row/decision checks passed, with the expected escalation-capability check false, but a disposition bug labeled this as `FAIL_AUDIT_DISAGREEMENT`.
- `AUDIT-02.json` is a separate corrected audit invocation over the same immutable raw. It reports zero attempt disagreements and the preregistered `HOLD_UNREPRESENTED_RISK_ESCALATION`. It imports the independent row checker from `audit.py`, not `candidate.py` or `coverage.py`.
- Inspection of raw showed that the formal duplicate proposal was rejected first as an extra non-OPTIONAL row, so it did not isolate the semantic-duplicate gate. The first post-formal duplicate supplement (#02) also stopped because its positive-control setup itself contained the duplicate; its invocation and failure log remain at `results/duplicate-control-02/`.
- Corrected targeted construction #03 used the unchanged baseline plan as the positive control and appended an OPTIONAL row with a new ID but identical primitive/subject/evidence-role as the negative control. In the pinned container, baseline was accepted and the duplicate rejected specifically with `duplicate or conflicting semantic check`; `PASS_TARGETED_CONSTRUCTION`. It did not replay the formal allocation or alter `RAW-01.json`.

These preserved issues narrow the conclusion; neither failed audit label nor failed supplement is deleted or rewritten.

## Artifacts and hashes

- Formal raw `RAW-01.json`: SHA-256 `78d6cdd142191a05b70c09e78cdace80a8413613737bba58a6f8311cb96dd2b5`
- Initial audit `AUDIT-01.json` (historical classification bug preserved): `3e94f6382cc730ebfda9d69df0144ae5b951734506e4e22cda4ce2d041b0adfb`
- Corrected audit `AUDIT-02.json`: `06d5048a74f1bbc266d30ed433dea247db049bd191febc0a30950eff5bfee162`
- Duplicate construction #03: `e0eea1436320f9ac5ff01126bccc59fd8b17f3c10856d2bd47db585548466783`
- Formal command receipts, exact argv, streams, hashes, and exit codes are under `results/formal-01/`.

## Limits and next decision

The finite acceptance boundary is relative to this hand-authored corpus/oracle. It does not show real Agent Action coverage, policy completeness, current evidence, true effect, safe action, registry authenticity, production deadline feasibility, or reduced verification cost. `unknown_check_required` remains explicit but cannot discover omitted ontology concepts; #5275 owns that.

The next research decision is a small contract bridge with #5266 and #5273: identify the exact typed risk/escalation requirement and its authoritative input/owner, then test it in an additive successor. Do not add that requirement to frozen IR v0.1 retroactively, and do not claim the complete #5269 H/D until the bridge is frozen and tested.
