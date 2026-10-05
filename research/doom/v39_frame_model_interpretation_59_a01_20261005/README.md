# V39 saved-frame model interpretation — Issue #59 A01

This is a single-invocation, saved-image probe of whether the selected Codex model can
read a threat-visible V39 frame and its HUD. It tests model comprehension of a
single image, not observation delivery, timely reaction, controller behavior,
game effect, or MAP01 completion.

## Frozen hypothesis and gates

- **H:** Given only V39 sequence 200's 1280×800 PNG, Codex CLI 0.146.1 using
  `gpt-6.1-sol` at medium effort will identify the visible hostile and read
  health/ammo exactly.
- **T:** Attach only the retained sequence-200 PNG to one non-interactive
  `codex exec` call. No game, GUI, controller, follow-up, or retry.
- **D:** `PASS` requires schema-valid JSON, `visible_hostile=true`, health 51,
  and ammo 38. A completed call with any incorrect/missing field is `FAIL`.
  A CLI/model/service failure, malformed response, or missing raw evidence is
  `STOP`; preserve it without rerunning this allocation.
- **C:** The model may infer a threat from a single screenshot while still
  failing to distinguish a target, HUD digit, or suitable response. The typed
  observation can also be wrong; it is an independent source for HUD values,
  not proof of game truth.
- **U:** One frame and one call do not estimate reliability, latency benefit,
  generalization, or live-control effectiveness. The cover recommendation is
  descriptive and unscored. No action is executed.

The immutable input is `source.png`, copied from current-main V39 run
`map01-v39-coast-liveness-live-01/runtime/200.png`. Its PNG SHA-256 and source
event digests are recorded in `freeze.json`. `prompt.txt` and `output.schema.json`
are part of the freeze. Redacted CLI JSONL/stderr, final-response absence,
exit status, source provenance, and independent audits belong beside this file.

This probe is distinct from open PR #7950, which exercises a synthetic
frame-identity/API boundary without pixels or a threat classifier, and PR
#7913, which preserves frame-color proxy and typed-health boundary evidence
without a model or GUI. PR #7987 later used the same image for a loopback
`turn/steer` protocol test without inference. This package attempted the
selected model's interpretation of one actual retained V39 screenshot; the
client STOP left comprehension unevaluated and does not close either
live-response gap.

## Result

The one frozen CLI invocation exited 1 before returning any model response.
The authenticated local Codex CLI 0.146.1 rejected `gpt-6.1-sol` for the
ChatGPT account with HTTP 400 (`model is not supported`). The independent audit
returns `STOP`; screenshot comprehension is **not evaluated**. This is useful
client/model-availability evidence only. The selected model, CLI, and input
were not changed and the consumed allocation was not retried. See
[`REPORT.md`](REPORT.md), [`RESULT.json`](RESULT.json), and the preserved raw
files under `raw/`. Original logs remain locally in the ignored, mode-restricted
`raw/private-local/`; only redacted copies are published.
