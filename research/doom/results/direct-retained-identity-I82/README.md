# PR #7356 intent-token absence guard — I82

**Disposition: `PASS_NARROW_IDENTITY_GUARD_CONSTRUCTION`; live telemetry remains gated.**

## H / T / D / C / U

**H.** A direct retained-input result is ready only when both paired events carry an intent token and the token/key match. An omitted or null token must not be treated as a shared identity.

**T.** Download the candidate analyzer and existing tests from PR head `7c99d8cb9203e574194e76c0e8384255aaa82d2d`, add absent/null admission and release regression cases, preserve the first run against unchanged source, then run the focused suite and an independent audit of the eight-case matrix.

**D.** Pass if both missing-field and explicit-null false accepts become not ready and readiness for all six other cases is preserved; no unrelated timestamp behavior changes.

**C.** The documented telemetry contract requires paired rows carrying the same intent token and key. It does not currently specify whether empty strings or non-string token values are valid. Those are retained as exploratory matrix cases and not changed by this narrow patch.

**U.** This validates parser construction only. It does not validate emitted live event identity, common clock provenance, physical release, useful feedback, or integrated MAP01 behavior.

## Results

Regression-first run against the unmodified PR analyzer failed the absent and null admission-token subcases (expected red). The narrow guard now records invalid admissions and rejects null/absent release tokens before matching. The exact focused suite passes **9/9**; `py_compile` passes. The independent before/after matrix audit found both identity false accepts repaired and all six other case outcomes preserved (`PASS_NARROW_IDENTITY_GUARD`, zero errors). Existing timestamp-order tests remain included.

Commands from repository root:

```powershell
python -m unittest -v research.doom.test_analyze_map01_direct_retained_input_v1
python -m py_compile research/doom/analyze_map01_direct_retained_input_v1.py research/doom/test_analyze_map01_direct_retained_input_v1.py
python research/doom/results/direct-retained-identity-I82/audit_identity.py
python research/doom/results/direct-retained-identity-I82/audit_patched_identity.py
```

No producer, X11, game, input dispatch, model, or formal allocation ran.
