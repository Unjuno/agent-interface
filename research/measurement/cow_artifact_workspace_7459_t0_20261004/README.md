# Issue #7459 — OrbStack COW artifact workspace T0

## H / T / D / C / U

**H:** For a tightly scoped, quiescent local-file workflow, a private COW workspace can produce an exact independently auditable artifact delta without pre-promotion writes to its base; uncertain or incomplete state must be refused. A pass is only for the tested synthetic container route.

**T0:** Compare a disposable direct-live control, a versioned private-copy draft control, and an OrbStack Docker-managed writable container layer based on a pinned read-only image. Exercise single-file edit, multi-file edit/create/rename/delete, metadata-only change, interrupted multi-file save, dirty/open-buffer analogue, concurrent base-revision change, and an attempted network effect. Capture `docker diff`, exported bytes and modes, container configuration, all command exits, input/source/image identities, and decisions. The dirty-buffer and stale-revision cases are refused before launch because filesystem bytes cannot establish their semantic state. No GUI app, model, human, host-artifact mount, user volume, or external network sink is used.

**D:** `METHOD_PASS_SCOPED` only when clean single/multi-file cases produce the exact expected independent byte/delta result, all pre-promotion base fixtures remain unchanged, and partial/stale/dirty/effect cases refuse. Any silent base write, missed conflict/effect, or wrong delta is `FAIL_CONTAINMENT`. If the tested effect/consistency boundary cannot be audited, disposition is `HOLD_NO_CONSISTENCY_OR_EFFECT_ORACLE`. The independent auditor must reject planted delta/hash/decision corruptions.

**C:** Native app drafts or sequential/context-restored interaction may be simpler and more reliable. Docker's layer may accurately retain bytes while failing to capture application memory or effects outside its network/process boundary.

**U:** One deterministic fixture and one OrbStack Linux/aarch64 engine only. This does not test macOS host APFS COW, actual GUI buffer/save behavior, arbitrary plugins/IPC, remote state, human usability, or automatic promotion. In particular, no result here is a security claim about arbitrary GUI applications.

## Ownership and source freeze

- Issue: [#7459](https://github.com/Unjuno/agent-interface/issues/7459); no Issue comments/owner allocation and no matching PR or branch were found in the preflight search.
- Main frozen at `93090bcbf0c9eb0cd5f6feeb4abd2477e8453202`.
- Additive package: `research/measurement/cow_artifact_workspace_7459_t0_20261004/`.
- Backend: OrbStack Docker, Linux/aarch64, `overlayfs`; pinned Alpine manifest `sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8`.
- Nested OverlayFS mount construction probe failed with `Invalid argument`; this is retained as a setup boundary and is not the tested COW backend. The experiment uses Docker's own container writable layer and independently checks it with `docker diff` and `docker cp`.
- No Docker image removal, volume cleanup, user-volume access, or cleanup of unrelated containers is part of this protocol.

The exact source and runtime digests are recorded by `freeze.py` in `raw/freeze.json` before the one formal candidate run. `candidate.py` refuses to start if those frozen source hashes have drifted. The independent `audit.py` does not import the candidate.

## Reproduction

From this directory, with the pinned image already available in OrbStack:

```sh
python3 freeze.py
python3 candidate.py
python3 audit.py
```

The candidate builds only from the local pinned image (`--pull=false --network=none`), creates uniquely named containers with `--network none --ipc private --pids-limit 32`, and uses no host artifact bind. It preserves raw outputs under `raw/`. A nonempty raw directory, occupied image/container name, source drift, or candidate infrastructure error is a STOP; do not rerun over the retained first outcome.

## Result

Pending execution. Do not infer PASS from construction or from Docker's overlayfs storage-driver label. The formal decision is `raw/audit.json` plus this report's later result section; all failure and setup evidence is retained.
