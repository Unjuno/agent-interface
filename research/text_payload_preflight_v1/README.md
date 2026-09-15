# Whole-payload text preflight — research candidate

Preflight the complete text and read-only keymap before emitting the first key. Lower only printable ASCII present at first-group levels 0/1; derive Shift explicitly. No clipboard fallback, remap or normalization. This is **not** generic Unicode `input.text`, an IME, or a systems-runtime port.

Dependencies: Python 3.13 tested, python-xlib, Tk 8.6, Xvfb, xauth, Openbox. Writer transfer additionally uses LibreOffice 25.2.3.2 (gen VCL), odfpy for the fixture seed; standard-library ZIP/XML for post-execution scoring. A fresh authenticated display is allocated with Xvfb `-displayfd`, TCP disabled. Only owned child processes are terminated.

From repository root, with a NEW absolute output path for every invocation:

```sh
python3 -m unittest discover -s research/text_payload_preflight_v1 -p 'test_*.py' -v
python3 research/text_payload_preflight_v1/run.py --baseline research/runtime_backend_x11_v0/backend_x11.py --source-commit <exact-checked-out-source-SHA> --out /absolute/new-gui-result
python3 research/text_payload_preflight_v1/writer.py --baseline research/runtime_backend_x11_v0/backend_x11.py --source-commit <exact-checked-out-source-SHA> --out /absolute/new-writer-result
```

`--source-commit` is recorded provenance supplied by the caller, not an automatic checkout attestation. Verify committed source hashes before execution; the baseline blob is enforced. Intended side effect is text insertion at current caret; focus acquisition/reset/save are separate fixture actions. Freshness counters are supplied, not sensed. No midflight rollback or hard-kill release guarantee.

## Integration boundary

PR #226's coarse `ASCII` route should not be advertised as complete payload coverage. Bind a route to implementation identity, actual text, representable symbols, initial state and declared side effects before dispatch. An error after emitting a valid prefix is not safe fallback eligibility: redispatching the whole text could duplicate the prefix. This candidate does not implement retries.

## Interpretation units

Pacing is seconds in Python (0.012 s = 12 ms), timestamps and elapsed diagnostics are integer nanoseconds. Symbol/keycode IDs and trial counts are dimensionless. Keycode ranges are 8..255; supported text code points are 32..126. The plan's conversion and validation never treat a keycode as a Unicode character. No confidence interval, energy or speedup claim is derived from this finite conformance matrix.
