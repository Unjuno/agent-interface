# Astra camera-stabilized cue A01

**Result: `FAIL_WALL_CUE_NOT_SUPPRESSED`.** Integer translation registration did not remove the reference warm-pixel trigger at video 22.7 s: the unregistered count was 186, and after a measured `[12, 0]` pixel shift the registered count remained 186. Both exceed the frozen threshold of 40. The independent reconstruction passed with zero errors, and its unregistered counts match the prior A01 vector exactly.

This is a narrow diagnostic of one translation-only method on ten frames from the retained, edited Astra video. The visually described wall-indicator label comes from the two-frame review in [PR #7913](https://github.com/Unjuno/agent-interface/pull/7913); this package does not independently classify the pixels. The pre-window 21.9 s muzzle-flash cue also remains unchanged at 96 pixels. A later 23.1 s row reaches the ±16 px search boundary, so its reduction from 176 to 145 is not interpreted. The result rejects this frozen translation-registration hypothesis only.

## Freeze and reproduction

- Current-main freeze: `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`.
- Source video: `research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4`, SHA-256 `201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4`.
- Reference A01: PR #7913 head `3cd63cd8c7fa1debbab743294e2056d987c4725f`, raw SHA-256 `b6fee496a45ec9d88a6d50b060cbfef2c781fa8d44020d80542b9ba8f77a9e27`.
- Source RGB extraction contains ten 320×280 frames at 5 fps; `frames.rgb` SHA-256 is `e0ce64678e5a246186c442a1bf88a3d34bb6d52d721438dde9a3e7b8e941a8b1`.
- The candidate ran once and exited 0. The separate auditor ran once and exited 0 (`PASS_RAW_RECONSTRUCTION`). No retry occurred.
- Host execution used macOS Python 3.14.5, NumPy 2.5.2, and FFmpeg 8.1.2. OrbStack Docker server information was available, but image inventory stopped on an unsupported containerd blob read error; no image pull or container run was attempted.
- Before the one-shot candidate, the three synthetic registration construction checks passed. They do not test visual semantics.

From the repository root, rerun the **retained-data derivation only** with:

```sh
python3 -B research/doom/astra_camera_stabilized_cue_a01_20261005/candidate.py \
  research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4 \
  research/doom/astra_camera_stabilized_cue_a01_20261005
python3 -B research/doom/astra_camera_stabilized_cue_a01_20261005/audit.py
```

The commands above reproduce the retained-data calculation; they are not authorization to repeat the one-shot candidate. Exact parameters and adjudication are in `FREEZE.json`; raw frame bytes, row-level output, audit, invocation record, and hashes are retained in this directory.

## Scope

No enemy classification, current-main V39 runtime response, game/model/GUI/OS-input execution, physical key release, useful feedback, recovery, ammo/progress, terminal task effect, survival benefit, or MAP01 completion was tested. Issue #59's live-threat exposure remains unassigned and is a distinct gate; this package grants or consumes no live allocation.
