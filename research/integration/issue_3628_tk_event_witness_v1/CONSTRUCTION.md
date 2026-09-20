# Issue #3628 — passive Tk key-event witness construction

This is a construction gate for the new successor, not a formal public-MCP
allocation. It preserves #3587, #3618 and #3620 unchanged.

The frozen #3618 fixture registers `<Control-s>` on Tk's `all` bindtag and
returns `break` from its save handler. Its generic `<KeyPress>` logger is also
registered on `all`; the more-specific shortcut handling prevents that logger
from recording the `s` keysym. The saved effect and final image exist, but the
preregistered input-event gate correctly remains HOLD_OR_FAIL.

The candidate changes only instrumentation order: `AgentInterfacePassiveKeyWitness`
is inserted into the Entry's bindtags immediately before the `Entry` class tag.
It observes KeyPress events and returns `None`, allowing class and `all`
bindings to proceed unchanged. Each event carries a monotonic timestamp; the
effect receipt records the save callback timestamp so an independent check can
require the witnessed chord to precede the independently observed effect.
Effect callbacks are append-only JSONL with a callback count so duplicate saves
cannot be hidden by overwriting the receipt.

`test_tk_order.py` uses `event_generate` under Xvfb to verify that the passive
tag sees `Control_L` and a Control-modified `s` before the later `all`-tag
handler returns `break`, while the save effect still occurs exactly once.
`audit.py` and `test_audit.py` cover missing, duplicate, reversed, unmodified,
intervening-key, wrong-marker, no-effect, duplicate-effect, bool/int type
confusion and effect-before-witness mutations. These checks do
not establish that the public MCP/physical X11 injection path delivers the
same event sequence; that requires the fresh allocations preregistered in
Issue #3628.

## Construction result (2026-09-21)

- The unchanged production fixture blob is `2198b203ca360607c649810bf3f4acacb5362fde`
  at both embedded source revision `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`
  and tested main `961f14b836e549ca5f6cfb6bf3ef4b470e91b1b5`.
- WSL Ubuntu 24.04.4 / Python 3.12.3 / Tk 8.6 / Xvfb:
  `xvfb-run -a python3 -m unittest discover -s
  research/integration/issue_3628_tk_event_witness_v1 -v` — 11/11
  pass. The test imports `configure_fixture` directly, maps and focuses the
  Entry, injects a synthetic Control_L then Control-modified s KeyPress, and
  verifies the event witness and save effect. The ten raw-audit controls pass.
- Windows Python: 10/10 raw-audit tests pass; the X11/Tk event test is skipped
  by design. `compileall` and `git diff --check` pass.
- A first Xvfb test-harness attempt kept the Entry unmapped and observed no
  generated events. That harness-only failure is retained here; the test was
  corrected to map/focus the Entry and then exercised the fixture itself.
- Supplemental WSL/Xvfb Python-Xlib XTest probes were construction-only, not
  formal allocations. `construction-xtest-01` stopped before sending any input:
  this Python-Xlib TranslateCoords reply exposes `x/y`, not `dst_x/dst_y`;
  the fixture was reaped, with zero events/effects. `construction-xtest-02`
  corrected that property access and sent the pointer/key sequence, but the
  fixture recorded zero button/key events and no save receipt; it was reaped.
  Both immutable result receipts and manifests are retained. These results
  reject any claim that the direct XTest route was validated; they do not
  affect the separately completed PR #3636 formal MCP allocations.
- No MCP client, actual XTest/MCP input, container, OrbStack allocation, or
  formal task was run by these supplemental probes. This is a Tk instrumentation
  construction result only.
