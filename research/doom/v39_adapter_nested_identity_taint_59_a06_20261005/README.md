# V39 nested/outer adapter identity taint — A06

## H / T / D / C / U

**H.** A duplicated adapter edge whose outer `intent_token` conflicts with the nested adapter token must taint both identities; it must not split into an incomplete foreign group while leaving the original pair complete.

**T.** Freeze #7690 A05 candidate head `a3155bec0b21d29557dbd4bd3d7218eb039cb135` and retained A01 fixture. Run existing exact, unknown-event and legacy-transition regressions plus duplicate DOWN and UP rows with only their outer token changed.

**D.** Baseline should return paired timing for both conflict mutations. Candidate must pass all four targeted methods and return no paired adapter receipt for either conflict. Existing prior cardinality boundaries remain closed.

**C.** Exact hashes and baseline/candidate output are in `A06_RESULT.json`; the separate raw/source-derived audit is `A06_AUDIT.json`.

**U.** One retained synthetic fixture and deterministic projector only. It establishes no physical release, live X-server state, application consumption, task effect, threat response, recovery or MAP01 result.


## Auditor correction

The first independent audit attempt is retained as `A06_AUDIT_ATTEMPT1.json`. It failed because its expectations incorrectly included A05 unknown-event and legacy-transition failures, which the frozen A06 baseline already contains fixes for. The corrected audit v2 checks only the two preregistered A06 outer/nested token-conflict cases. The candidate replay was not repeated.


The first two audit attempts are preserved as `A06_AUDIT_ATTEMPT1.json` and `A06_AUDIT_V2_ATTEMPT1.json`; both failed on audit-expectation defects, not candidate execution. Audit v3 directly evaluates the frozen baseline and candidate projector functions against the raw-derived two token-conflict mutations. No candidate runner rerun occurred.

The retained package verifier also passes 81 checks over 42 entries after rebinding its live-source check to A06.
