# V39 A03 audit seal correction A01

This additive audit-only successor repairs one source-identity claim in the A03 audit-v2 package. It does not edit the original A03 package or reclassify its one-shot result.

## H / T / D / C / U

- **H:** The A03 v2 test is exactly identified by its committed bytes, and a versioned correction can bind those bytes while retaining the earlier incorrect digest as history.
- **T:** Read the exact PR #7774 head copies of `FREEZE-AUDIT-V2.json` and `test_a03_v2.py`; compute their byte lengths and SHA-256 values; run the three retained raw-audit tests and the two new seal-correction controls. Do not invoke `probe_a03.py`.
- **D:** PASS only when all five tests pass, V3 records the exact test and verifier identities, and the predecessor freeze, candidate freeze, raw, and result remain byte-identical. A mismatch or test failure is STOP.
- **C:** This repairs the audit source seal and replays a deterministic retained-raw audit only. It does not establish fresh main composition, live deployment, X11 behavior, useful feedback, bounded recovery, threat response, or MAP01 progress.
- **U:** No candidate invocation, model call, GUI, OS input, game, or live allocation.

## Finding

The immutable A03 package at PR head `535254f816eff34755722067e646f9071d69b22a` contains a 1,212-byte `test_a03_v2.py` whose SHA-256 is `14ececdbeb241c953fa2986edfda4f5cecf12fb1c94f89ef47c4c3b450d67ddd`. `FREEZE-AUDIT-V2.json` declares `7fda2f70d5406cb9ad6317ce58456a582cda42932005a4a8feeb76be5e57b0a6`. The V2 file and claim remain unchanged. `FREEZE-AUDIT-V3.json` binds the observed bytes and names the superseded claim.

## Reproduction

From repository root, with WSLc and the pinned `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` image:

```sh
wslc run --rm --network none --cpus 1 --memory 512m --volume "$PWD:/repo:ro" --workdir /repo/research/doom/map01_v39_perkey_bridge_a03_down_cleanup_race_20261005 python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B -m unittest -v test_a03_v2
wslc run --rm --network none --cpus 1 --memory 512m --volume "$PWD:/repo:ro" --workdir /repo/research/doom/map01_v39_perkey_bridge_a03_audit_seal_correction_a01_20261005 python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B -m unittest -v test_seal_correction_v3
```

The validation image here is Python 3.12.15 / linux/amd64; the original A03 candidate used a separately pinned Python 3.12.11 / linux/arm64 image. This successor does not claim to reproduce that candidate environment or execution.

## Current PR-head recheck

Before publication the PR branch advanced to `b4e66975a2383f98c83d3b8d0c8947d2c1db39b6`. All 21 files in the retained A03 package were read from that exact head. Every pinned A03 source hash still matches, including the 1,212-byte test at SHA-256 `14ececdbeb241c953fa2986edfda4f5cecf12fb1c94f89ef47c4c3b450d67ddd`; the V2 mismatch remains. This static recheck did not rerun the candidate or tests. The V3 correction tests already ran on byte-identical A03 inputs at the predecessor head.
