# V39 → V15/V12 synthetic composition run (A01)

**Outcome: `PASS_CONSTRUCTION_SCOPED`.** This package executes the real V39 controller, child V15 session, V12 delegation, V13 Executor, typed backend, and owner lifecycle through a one-decision synthetic run. The game/VizDoom, planner, image capture, and Xlib server are fakes. This establishes that these code paths compose under the exercised fixture and that their emitted records reconcile. It says nothing about live threat exposure, MAP01 task effect, benefit, physical key actuation, or application consumption.

## Reproduce

Requires Python 3.12 with Pillow and NumPy. From this directory:

```sh
PY=/path/to/python3
WORK="$(mktemp -u /tmp/v39-full-repro-XXXXXX)"
export V39_SYNTHETIC_SOURCE_ROOT="$PWD/candidate-source"
export V39_SYNTHETIC_WORK="$WORK"
export PYTHONPATH="$PWD/reproducer:$PWD/candidate-source:$PWD/candidate-source/research/doom:$PWD/candidate-source/research/live_control:$PWD/candidate-source/research/observation_gating"
"$PY" reproducer/run_full_v39_v15_synthetic.py
```

The runner prints `PASS_CONSTRUCTION_SCOPED` only after it sees the actual release transition, simulated server KeyPress and KeyRelease, and an empty final fake-server keymap. The generated output path is printed in its JSON result. To audit the archived run and source snapshot, run `python3 audit.py` here; it checks all source SHA-256 and Git blob hashes, five typed/full observation reconciliations, the admission/release pair, fake-X trace, final owner cleanup, score, and child stderr.

Focused regression suite, from `candidate-source/research/doom`:

```sh
PYTHONPATH="../..:.:../live_control:../observation_gating" "$PY" -m unittest test_v39_measurement_session_comp test_map01_v15_perkey_backend_selection test_map01_overlap_controller_v39
```

The packaged candidate sources are identified in `candidate-source-manifest.json`. Provenance inputs: current main `24cbb631b972eee1723d2372adf53032dfdaab20`; PR #8094 head `88e8099de97de12c29fcf3db0cb374b160a27ead`; merge-tree `7d3bdbc34f68c4d619990bafab7912112d803010`, with the controller conflict resolved by retaining main's verified-empty terminal release and PR #8094's planner-interrupt reuse path. This is a synthetic integration candidate and does not modify or claim a merge of PR #8094.
