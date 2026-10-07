# V39 input acknowledgement-loss cleanup A02

On frozen current-main source, one normal F8 press/release completed one step with an identity-bound per-key release receipt. In the treatment, the fake provider applied the KeyPress to keycode 38 and then raised `OSError` before acknowledging the owner RPC. ExecutorV13 marked the step failed with zero completed steps, emitted no explicit up transition, and ran terminal owner cleanup. That cleanup sent one KeyRelease, recorded a verified empty owner state before the terminal, and left the fake keymap empty.

This supports only a bounded construction finding: the selected software path cleaned up a delivered-but-unacknowledged keypress in this deterministic fake-X test. It does not show physical keyboard state or an application effect. The behavior remains subject to independent review and any broader live-control evidence.

See `PROTOCOL.md`, `FREEZE.json`, `SOURCE_MANIFEST.json`, `RESULT.json`, `AUDIT.json`, and `results/raw.json`.
