# V39 selected keyboard release path A01

## H / T / D / C / U

**H:** The current V39 keyboard path inherits `session_v5.raw()` and installs the exact V10 `InputOwner`. Per-key `down`/`up` calls reach XTEST and `sync()` but do not sample the keymap; `session_v5.release_all()` performs one aggregate owner release and keymap sample after the program's explicit key-ups. If that aggregate sample fails, release must remain unverified; owner close may later recover and verify neutral state.

**T:** Invoke the exact `session_v5.Backend.raw()` and `release_all()` methods with the exact `input_owner_v10.InputOwner` source and an in-memory fake X display. Run one clean two-key reverse-order release control, then one otherwise-identical case with a single failure at the aggregate release keymap query. Retain XTEST edges, sync/query order, emitted events, backend state, owner records before and after close, and cleanup outcome. Freeze the current V39 session/backend/owner inheritance source hashes. No X server, ViZDoom, GUI, model, Docker, or OS input starts.

**D:** `PASS_SELECTED_KEY_PATH_CONTRACT` requires both cases to preserve down/down/up/up ordering with no keymap query between per-key ups. The control must return a verified-empty `owner_release`. The fault case must retain the first query failure and must not treat it as verified; close-time recovery must be reported separately and must stop the owner with verified-empty state. Any source/hash mismatch or other outcome is `STOP`/`FAIL`; the candidate runs once and the auditor runs once.

**C:** The method and owner implementations are actual frozen source, but the Xlib/XTest server is in memory and only the selected backend methods are called. This does not launch the full V39 controller/session or prove server delivery.

**U:** No real X server, task effect, useful feedback, threat response, bounded recovery in MAP01, physical keyboard state, or hard latency bound is measured. A V10 aggregate owner release is not a per-key physical-release measurement.

## Reproduction

From the repository root, run the candidate once, then the independent raw-only audit:

```powershell
python -B research/doom/map01_v39_direct_key_release_a01_20261005/candidate.py
python -B research/doom/map01_v39_direct_key_release_a01_20261005/audit.py
```

Outputs are write-once under `results/candidate-a01/`. The candidate refuses to overwrite an existing output. The auditor verifies frozen source/package hashes and recomputes the retained cases without importing or rerunning the candidate.
