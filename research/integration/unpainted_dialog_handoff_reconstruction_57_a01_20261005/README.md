# Readme — #57 unpainted-dialog handoff reconstruction A01

This is an offline, posthoc reconstruction of the existing `recovery-assistant-01` Calc trace. It isolates four adjacent images around the unpainted format dialog, recomputes PNG pixel differences and image-ready timestamp intervals, and carries forward the original audit's task and release scope. It is not a new GUI run or a formal experiment.

`test_replay.mjs` runs the actual `runtime/host_v1` primary caller and instrumented relay against a temporary deterministic MCP child that serves the four retained PNGs. It checks exact image delivery, source-bound review receipts, two one-time input dispatches, and explicit observations after the unresolved and stale frames. The first raw relay record is retained under `replay_raw/a01_20261005/`; `audit_replay.py` independently checks the request order, byte-exact images, fixture release receipts, reviews and separation from the original independent task score. It uses no GUI, model/provider, Docker, live allocation or new production code.

Run from the repository root with Python and Pillow:

```powershell
python research/integration/unpainted_dialog_handoff_reconstruction_57_a01_20261005/analyze.py
node --test research/integration/unpainted_dialog_handoff_reconstruction_57_a01_20261005/test_replay.mjs
python research/integration/unpainted_dialog_handoff_reconstruction_57_a01_20261005/audit_replay.py
```

The analysis validates pinned SHA-256 values for the JSON inputs, selected PNGs and analysis/replay/audit scripts against `SHA256SUMS`, checks selected frame timestamps/focus flags, verifies the existing audit summary, computes pixel differences from decoded RGBA bytes, and joins each response to its originating command and terminal record. The byte-wise pixel count avoids newer Pillow-only APIs. Source trace and images remain unchanged.

To create another retained raw run, set `HANDOFF_REPLAY_CAPTURE` to a new, nonexistent directory before running the Node test; it refuses to overwrite existing evidence. `REPLAY_SHA256SUMS` pins the retained run.

Result: #006 has the modal window in window-list context while the image is unpainted; #007 is painted; #008 still shows the dialog after the confirmation action and its focus samples disagree; #009 shows the worksheet. Image-ready deltas are 16,034.582 ms, 7,045.820 ms, and 8,557.071 ms. Pixel changes are 11.7682%, 0.2426%, and 11.9498% respectively. From request receipt to image-ready, #006 took 499.111 ms, #007 79.421 ms, #008 96.537 ms, and #009 79.846 ms. The confirmed-key program's terminal release followed image readiness by 26.252 ms; observation-only terminal releases followed by 17.995 ms and 16.969 ms for #007 and #009. The next command arrived 8.480 seconds after #006, 6.949 seconds after #007, 8.477 seconds after #008, and 6.006 seconds after #009 (the #006 successor was a clock request).

Interpretation stays narrow: the host produced images quickly after these requests, but intervals between requests were much longer and mix model reasoning, orchestration and other activity. The trace cannot establish exact useful-feedback onset, causal wait savings, general reliability, or a default wait/sensor policy. Original audit reports 9 exact frames, 4 completed programs, successful saved values `[222, 440]`, verified releases, and owner shutdown with release.
