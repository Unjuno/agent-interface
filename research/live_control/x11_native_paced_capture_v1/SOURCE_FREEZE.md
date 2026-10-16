# Issue #3949 — source-first formal freeze

Base main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Allocation: `native-paced-capture-20260922-01`.
Branch: `research/x11-native-paced-capture-20260922-v1`.
Formal invocations at this freeze: **0**.

The complete local source/build/environment/construction package has been assembled before any formal sampling. Its immutable archive is `source_bundle.tar.xz`: 29,964 bytes, SHA-256 `85eb6fe450ddfac4f9971134cbd69d3a687a7ea7d5b8865660ad1a8643da68b4`. The archive contains 32 files. Its lossless base64 transport has SHA-256 `da8fe8df9bedbb8e25bb6eb793e559cb5c9f589e2af2d59732cc0da5c3d0b9f6`. Archive transport publication follows separately; this commit records the prior hash/time boundary, not a claim that the archive is already on GitHub.

`FREEZE.json` SHA-256: `733dcf476cd60b28b6617d7ac2502e82059966ab3f7780ca1b3ebd0675e1b6e8`.

| Frozen file | SHA-256 |
|---|---|
| src/native.c | 3ecf26f800e9cf7cd28ac57f33cdf5020dfa4f014b3a1662cc8ac4771227713e |
| src/native.so | 3dae5fce9a3ad12787835cf5e6a1fca6c4cefa5d29a5bf485cd863a4a1113614 |
| src/fixture | 7dd4e36bc2e41bee92e04e44a9b77e8f2cd64b149c0bd78023c52fbe3435d75e |
| src/study.py | aaf20c84ab41ecf654058f3e4dad6f55d294b644687638974cb5b3172d6b7630 |
| src/audit.py | f2c0011b9a36b35cbb378356f8dc7690f876dfd85a1a010ce33646a3a4c7f5a7 |
| src/test_audit.py | ad6e8d6b0aa5bc9e53b8d9523877c2e803992e6b9975302b2b5c214b31688f66 |

## Fixed experiment and decisions

Twenty matched pairs / 40 cases; balanced Python/native order; nominal 5 ms cue at offsets 120/122/124/126/128 ms repeated four times; 300 ms window; 2 ms non-catch-up cadence; 1 ms CPython switch interval; same native capture/count helper and CPU-bound Python competitor. Observer/load/Xvfb+fixture on allowed CPUs 0/1/2. This is the supplied Linux x86_64 execution container, CPython 3.13.5 with GIL; no Docker/OrbStack engine/image identity is claimed.

PASS_NATIVE_PACED_CAPTURE_SCOPED requires all 40 cases and integrity gates, all software cue exposures 4–8 ms, native detections >=18/20, median paired native/Python maximum capture-start-gap ratio <=0.70, and >=2 native-hit/Python-miss pairs. Complete integrity with a scientific gate miss is HOLD_NATIVE_PACING_BENEFIT_NOT_ESTABLISHED. Any source/setup/timeout/cleanup/cue-integrity error stops collection; preserve partial evidence and do not replace cases. No post-data tuning or retries.

Exact command from the bundle root:

```sh
python src/study.py run --mode formal --out formal
```

Independent audit, in a distinct process after collection:

```sh
python src/audit.py formal > AUDIT.json
python src/test_audit.py formal
```

## Excluded construction

Three cases total, not in the formal denominator. First construction stopped after one Python case because the auditor expected Xvfb exit -15 while the owned server exited cleanly with 0. That failure and its original source hashes/raw bytes remain unchanged. Before freeze, Xvfb cleanup was specified as reaped/not-alive and exit 0 or -15; fixture still must exit 0. Case timeout handling was also changed to terminate the whole owned process group. A fresh excluded matched pair then passed raw audit; the six-method suite rejected all 14 corruption variants. Thirteen native ABI/clock/null-handle/GIL checks passed. Scientific thresholds were not changed.

## Scope

This tests historical visual capture only. C returns a bounded buffer after the window; faster sampling is not proof of online delivery, fresh action authority, release safety, model/task utility, broad GUI reliability, cost savings, or hard real time. There are no keyboard/mouse/XTEST, model/provider, or experiment-network calls. No shared runtime or historical allocation is modified. #2117 and the project-wide roadmap remain open.
