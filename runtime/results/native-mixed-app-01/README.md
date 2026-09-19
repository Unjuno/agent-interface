# Persistent Calc/Inkscape round trip through native exchange

2026-09-20. Two primary-assistant runs use one private X server, two applications,
one NativeHandleBridge connection/session and the existing exchange/review route.
The assistant views each returned image and chooses each next action. No helper
model, controller oracle or direct application-file mutation chooses input.

## Failure discovered by composition

Run-1 (Calc seed 991090, Inkscape seed 991091) moved/saved the shape, switched to
Calc with Alt+Tab, entered [859,568], opened its format dialog, confirmed Excel
format and returned to Inkscape. Three native programs completed. The read-only
window handoff incorrectly adopted Inkscape's 1x1 InputOnly focus child as the
application surface: focus=surface=6291464, geometry [-1,18,1,1].

The assistant noticed this in the returned receipt, submitted no further target
input and explicitly finished. Saved files were correct (Calc [859,568], SVG
x=58), but this is NOT a successful return-surface binding. The failure remains
retained alongside the narrow saved-effect success; one score cannot replace
the other. Six retired-target probes refused with zero backend emissions.

## Shared fix and fresh use

focused_client_window reads the WM's _NET_CLIENT_LIST and walks the actual focus
ancestry, at most 64 links, choosing the nearest managed ancestor. Unknown lists,
invalid focus, cycles and read failures yield no candidate. It does not focus,
mutate the binding, create handles or grant input authority. The existing explicit
window review still checks focus, captures the new source and revokes all aliases.
There is no fallback to a guessed title, PID, or arbitrary child window.

Run-2 (Calc seed 991092, Inkscape seed 991093) repeats the round trip with new
values [324,455]. On returning, the receipt keeps child focus 6291464 but binds
application surface 6291463 with geometry [0,19,1280,781], the same top-level
surface as the initial image and a new binding revision/scope.

The primary assistant then grounds the moved shape from the new source, applies
two more Right chords, saves, views x=62, and explicitly finishes at stage 5.
Four native programs completed; independent saved workbook/SVG parsing confirms
[324,455] and x=62, y=50, width=40, height=30, no transform. Every program reports
verified neutral release. Ten retired-target probes (all prior targets after
each review) refuse with zero backend emissions, including the original Inkscape
target after returning to that same application. These probes are diagnostic,
not automatic repair attempts.

## Harness integration

The existing harness accepts --app calc-inkscape. It prepares both apps once,
starts with the last prepared app visible, keeps the same bridge, scores both
saved files only after explicit finish, and archives both outputs at cleanup.
Single-app Calc remains the default.

--max-stages 8 permits this five-stage exchange. The bound is explicit in an
immutable exchange-contract.json, constrained to 2..64; the default and historical
contract-free runs remain four stages. Out-of-bound or malformed contracts refuse
before request publication. This is a private caller contract, not extra input
authority. --probe-old-target also checks all prior stage aliases.

Reproduce setup:

```sh
PYTHONPATH=.:research/live_control python3 research/live_control/run_native_calc_self_use_v1.py \
  --app calc-inkscape --max-stages 8 --text-gap-ms 2 --probe-old-target \
  --seed 991092 --out results-local/FRESH-DIRECTORY
```

Use fresh presented sources to choose coordinates/actions; do not replay archived
requests into a new session. The mixed task goals name both applications.

## Evidence and limits

47 focused tests passed, including managed-ancestor/no-mutation behavior, absent
or cyclic ancestry, explicit longer stage bounds and malformed contracts. An
initial test-file insertion caused an IndentationError before test execution;
it was corrected before run-2 and the retained full suite passed.

archive-audit.py independently parses saved outputs and checks the ordered
binding revisions, source/request/reply correlation, all stale probes, release
rows, native program counts, terminal process cleanup and 122 image hash links.
SUMMARY.json keeps both runs and the ordered per-stage binding ledger. Actual
client metadata is retained without duplicate base64. Local combined calls in
run-2 took about 1.23-1.52 seconds including waits, captures and diagnostic probes;
these exclude host/model time and are not a matched speed result.

Cleanup recorded terminal return codes, including WM 1, Calc launcher 255 and
Inkscape -15. They establish teardown termination, not clean application exit.
Source holds final executed files; run-1 also retains its pre-fix harness/bridge.
Base: 2f29897227445b1e56ea72a2ccbb030701fa1417. SHA256.json covers every retained
file except itself; original absolute image paths remain provenance.

This is a concrete two-app persistent round trip, not the formal #2499 allocation.
Chromium, intentional geometry drift, window replacement, matched stable/
transition-only arms and injected missing/ambiguous/cleanup-failure controls
remain outside these runs. Do not label it PASS_MIXED_APP_LONG_SESSION_SCOPED.
It is not arbitrary-app reliability, human-tempo performance, model-token savings
or production promotion. Actual model usage is unavailable; helper calls were zero.
