# Layout-aware underscore input

Base: a924449f661d81bae88afc06fda5e0f3a41af673.

On a private Xvfb with Japanese keyboard layout, the old hardcoded
Shift+minus typed '=' instead of '_' into the Tk fixture and saved the wrong
URL. jp-held.log retains this failure. Underscore now uses the existing
live-keymap level resolver, like colon and formula symbols. An unsupported
level rejects before text emission.

The first jp.log is NOT Japanese-layout evidence: the X server reset to US
between setxkbmap exiting and the next client. probe-held.py keeps a display
connection open across the layout change. Its mapping records confirm JP
colon keycode 48 and underscore keycode 97. Both initial runs are retained.

jp-candidate.log verifies the fixed saved URL. suite-us.log and suite-jp.log
each pass 10 integration tests. native/result.json and its associated logs
retain the passing native suites. Unit cases cover underscore at either
supported level and refusal without emitting a prefix at unsupported levels.

Reproduce from repository root with Xvfb, setxkbmap, Tk and python-xlib:
    xvfb-run -a env PYTHONPATH=. /usr/bin/python3 runtime/results/x11-underscore-layout-01/suite-jp.py
    xvfb-run -a env PYTHONPATH=. /usr/bin/python3 runtime/results/x11-underscore-layout-01/suite-us.py

This does not explain or fix the earlier ambient-display colon-to-apostrophe
failure retained in x11-verify-preflight-01. It does not establish arbitrary
layout/group/IME support. These are programmatic native-input tests, not model
visual self-use, and do not measure latency, token cost, or human-speed parity.
