# Exact tile transport and actual assistant use

Research-only Python work after the scoped [A1 O1 result](../observation_gating/REPORT.md).
The frozen A1 sources remain unchanged. This directory adds an actual serialized
lossless transport, a live O1/O2 ablation, and a stdin interface used by the
assistant to choose GUI actions from reconstructed images.

- [Protocol](PROTOCOL.md): hypotheses, fixed policies, fresh seeds and hard gates.
- [Result](REPORT.md): 64/64 fresh tasks, 553 exact reconstructions, 70.73% same-trace wire reduction; no established local speedup.
- [Development and dogfooding](DEVELOPMENT.md): failures, changes and evidence.
- [Related work](RELATED_WORK.md): primary-source findings and adoption decisions.
- [Image preparation experiment](IMAGE_ARTIFACT.md): exact reference reuse, PNG latency/byte tradeoff and an actual-use timing gap.
- `tile_transport.py`: exact full/reference/tile packets and atomic receiver.
- `live_suite.py`: both transport arms use the same public controller.
- `motor_feedback.py`: Inkscape segmented drag observations, same in both arms.
- `analyze.py`: archived-wire, raw-PNG, metadata and saved-output audit.
- `dogfood.py`: interactive local stdin JSON session, not a scripted task solver.

## Run locally

Use Ubuntu/WSL with the A1 dependencies (Xvfb, Openbox, Python Xlib, Pillow, NumPy,
openpyxl, XTerm, LibreOffice Calc, Inkscape and a headful Chromium-family binary).
No model key is required for scripted experiments. The existing environment uses
Chrome for Testing 145 at the default path in the scripts; pass `--chromium` to
change it, and establish a new freeze if versions change.

From this directory in WSL:

```bash
python3 -m unittest -v test_transport.py
python3 dogfood.py --app calc --seed 790101 --out results/my-calc-session
```

The process returns a task goal, an image path and timestamped X11 context. Send
one JSON object per line. Inspect the returned reconstructed image to decide
the next action. Example commands (fill values from the returned goal):

```json
{"op":"text","text":"123","id":"type-a","wait_changed_ms":1000}
{"op":"key","key":"Return","id":"commit-a","wait_changed_ms":1000}
{"op":"chord","modifier":"Control_L","key":"s","id":"save","wait_changed_ms":1000}
{"op":"observe","id":"inspect"}
{"op":"finish"}
```

`input_ack` acknowledges X11 injection only. An observation includes independent
image-capture and context timestamps; they are not an atomic snapshot.
`wait_changed_ms` waits up to 0–5000 ms for a visual/context change relative to
the prior received state, and returns a timeout explicitly. A caret or a late
repaint from an earlier command can satisfy it: inspect the result. It never
claims semantic completion. `finish` permanently ends control before the saved
output evaluator runs. EOF or exceptions also close the private desktop.

An unchanged image reuses its existing PNG path. `.ait` packets and observation
metadata still advance. Changed frames are fully reconstructed before PNG/model
viewing, so this interface does not demonstrate image-token reduction. PNG disk
serialization and outer tool scheduling remain significant in this exploratory
adapter; its timings are not pooled into live benchmark timing.

The current interactive fixture supports four apps, a single modifier chord,
basic benchmark ASCII text and pointer drags. It is not the universal text/input
API promised by the long-term project. The ready message declares the exact
supported text characters; unsupported strings are rejected in full before input.
Unicode/IME and broader text are not implemented. No network endpoint is opened.

## Reproduce experiments

Every output path must be new. The checked-in raw directories are immutable
evidence; choose new names/seeds for another experiment.

```bash
python3 live_suite.py --phase development --pairs 2 --seed 741101 --out results/development-a2r2
python3 live_suite.py --freeze --out results/frozen-a2r2
python3 live_suite.py --phase fresh --manifest results/frozen-a2r2/freeze.json --pairs 4 --seed 770101 --out results/fresh-a2r2-r1
python3 live_suite.py --phase fresh --manifest results/frozen-a2r2/freeze.json --pairs 4 --seed 780101 --out results/fresh-a2r2-r2
python3 analyze.py results/fresh-a2r2-r1 results/fresh-a2r2-r2 --out results/a2r2-summary
```

The codec assumes an ordered reliable local channel and trusted bounded producer.
A lost packet or wrong base is rejected without mutating receiver state; start a
new stream with a full frame for resynchronization. In-process resync tests do
not establish network behavior. Every sample is captured in full; only transfer
representation changes. O1/O2 use equal zlib level 1, with actual packet byte
counts including headers/context. These are not PNG/API/token/cost comparisons.
