# Frozen audit-only successor A02 — Issue #6373

- Scope: independently complete the pre-registered downstream-success gate from A01's already frozen candidate/raw bytes. Do not rerun the candidate or alter A01 output.
- Normative source: Issue #6373 body SHA-256 `33899c3fe28ea8c5daddd478b7bbfb38db7afaf4c5bf3f8e8630c70dcfc143fd`.
- H/T: recompute each fixture's next-task success as zero mismatches on its frozen `next_requires`; compare eight-case success counts for RESTORE_PLUS_DIFF and SUMMARY_ONLY, while rechecking A01 safety outcomes from raw state.
- D: `PASS_METHOD_SCOPED` only if all 32 candidate mismatch counts match independent recomputation; every pre-registered preservation invariant still holds; and RESTORE_PLUS_DIFF succeeds on at least as many next-task fixtures as SUMMARY_ONLY. Otherwise FAIL/HOLD.
- C/U: `next_requires` is a stipulated deterministic fixture oracle, not observed GUI/human task completion. No causal, time, human, or application claim.
- One independent audit invocation; no candidate replay or retry. Exact input hashes are frozen in `FREEZE.sha256`: raw `91e1d8fcc3337a77539fb606221223678ee73c7b37f72d17e3fb74c851fcbdd2`; candidate `7cb86866a1186834ab20e63c4e953e6d83de9f376052bd46c70d379f3d1ed8dd`; oracle `6ff62297176697275f6ca03b615c0acf7699bc74d3ecafb90e26181e89be3348`.
