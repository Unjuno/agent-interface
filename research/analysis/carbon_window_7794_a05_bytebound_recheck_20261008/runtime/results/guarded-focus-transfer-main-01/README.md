# Main-specific guarded focus stop validation

Base: `4bf4cb04eade179be9f5a25b130ebe53ea3a71b7`.
Only the guarded key-press focus check and its two regression tests are applied
to main. No candidate caller, mint, move, or other candidate feature is required.
The [candidate discovery record](../guarded-focus-transfer-01/README.md) retains
the original collateral-input reproduction and all setup failures.

Before the two main-specific real X11 runs, FREEZE.json records hashes of the
fixture, adapted runner, bridge and unit test. Each has a fresh output directory
and owned Xvfb/Tk processes. Runtime source is unchanged between these runs.

- Transfer case: app moves focus from A to B 40 ms after click; after the 250 ms
  wait, guarded execution stops at text op 5 before keyboard emission. Neither
  A nor B gets a key. Completed pointer/wait prefix and neutral release remain.
- Stable control: no transfer; A receives exactly z, result completed, release
  verified neutral.
- Main-specific local native checks: 327 protocol tests and 143 harness tests
  pass. Full native logs/result are archived, separate from candidate checks.

This is a narrow correctness repair, not task recovery or general live control.
The new read-only X11 check has unmeasured overhead and a query-to-emission race
remains. Changes within the same target and already-held input are not covered.
It adds no background watcher/sensor, auto-refocus, replay or authority renewal.
It does not close #59 or claim useful model-feedback timing or human tempo.

```sh
python3 runtime/results/guarded-focus-transfer-main-01/verify.py
python3 -O runtime/results/guarded-focus-transfer-main-01/verify.py
```

These fresh-extraction audits are raw-only and never invoke GUI/input.
