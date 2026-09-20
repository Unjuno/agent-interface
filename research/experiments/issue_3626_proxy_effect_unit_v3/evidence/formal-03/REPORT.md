# Issue #3626 — formal-03 result

## Decision

`PASS_PROXY_BINDING_EFFECT_UNIT` for the frozen, deterministic GTK/Xvfb fixture unit only. One formal invocation produced 28 unique rows with zero runner exceptions and no retries. A separate network-disabled, read-only-source OrbStack/Docker audit returned zero errors and detected all four corruption challenges.

## Results

| Case | Rows | Observed result |
|---|---:|---|
| Positive effect | 4/4 | Exact GTK counter 0→1 and independently changed visible frame |
| Acknowledged no-effect | 4/4 | One click acknowledged, counter unchanged, yielded rather than reporting success |
| Stale version | 4/4 | Refused; zero emissions/effects |
| Replaced process/target | 4/4 | Refused; zero emissions/effects |
| Unavailable target | 4/4 | Yielded; zero emissions/effects |
| Ambiguous two-target control | 4/4 | Before dispatch, two ready PIDs and two distinct viewable XIDs were present; yielded with zero emissions/effects |
| Macro failure | 4/4 | Yielded; zero emissions/effects |

The root-window resource `query_pointer()` succeeded in 28/28 rows and recorded Button1 up. Process exit/reaping and X socket disappearance reconciled in the independent auditor.

## Frozen provenance

- Allocation: `issue3626-proxy-effect-unit-formal-03`; source commit `68dd2fbce9932123dc89e6b5d355b0c1b98c7d07`.
- Image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64; network disabled; root and source read-only.
- Raw JSON SHA-256: `29f1e301464217fe7987df05dc1181f9b854e41c3396d7cd01358447479619c4`.
- Independent audit JSON SHA-256: `bc05c69c2410e24a7caa5f3b941672f2c6a909de2668b6fa3bdc951c0ba171e8`.
- Preflight receipt SHA-256: `3e380f9089f70e0a4e86bf12e5db07b71eb0a9317c61b854bb60b36752c704e8`.
- Source-manifest SHA-256: `2d30089eb1ffc99ded760f5eb6840c0e1d68893e7bbd0b6198ba90bdefe226c5`; preregistration SHA-256: `f4e073b8337fecaecd8cd1aae7aa55c0126f97639d9b37f09dcf12d9d5e3dc03`.

## Scope limits

This does not compare models or people, establish usability, cost/token/latency benefits, a winning presentation arm, broad GUI safety, or production authority. It validates only this fixed fixture, operation, adapter, and pinned container execution.
