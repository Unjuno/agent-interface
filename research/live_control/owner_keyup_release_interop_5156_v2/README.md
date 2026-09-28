# #5227 synthetic release-schema compatibility audit

This is an additive, host-only successor to #5199. It does not change protocol v2 or its retained result. The v3 candidate accepts the six frozen owner cleanup reason literals, uses a string `key` for explicit `key_up`, and an exact integer `button` for `button_up`. It preserves the owner sequence, owned-to-empty, authority-false, and explicit synchronous caller-bracket checks.

The autonomous per-key rows and explicit receipts are synthetic schema cases, not records emitted by the pinned runtime. `input_owner_v10.py` currently emits a batched owner-release record without per-item released identities. Accordingly, a pass means only `PASS_SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY`; it is not evidence of telemetry interoperability, XTest execution, physical release, latency, or GUI behavior.

One local invocation, no retry:

```powershell
py -3.11 research/live_control/owner_keyup_release_interop_5156_v2/run_once.py --output research/live_control/owner_keyup_release_interop_5156_v2/results/result.json
```

The output path and sibling `audit.json` must both be absent. `run_once.py` checks pinned Git blob identities and source syntax/literals, writes raw results exclusively, and starts `audit.py` as a separate standard-library process. No Docker/OrbStack, LM Studio/model, GPU/CUDA, network, GUI/X11, or input dispatch is used.

