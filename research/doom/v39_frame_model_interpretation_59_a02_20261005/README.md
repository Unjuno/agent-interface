# V39 saved-frame model interpretation — Issue #59 A02

A02 is a separately frozen client-version successor to A01. A01's Codex CLI
0.146.1 run stopped before inference because its service rejected the requested
`gpt-6.1-sol` model. A02 changes only the client distribution to the verified
official `@openai/codex` 0.160.0 npm package; it reuses the exact prompt, schema,
model, effort, and retained screenshot. It runs once and cannot retry.

## H/T/D/C/U

- **H:** With Codex CLI 0.160.0, the current ChatGPT account accepts
  `gpt-6.1-sol` and returns schema-valid interpretation of V39 sequence 200.
- **T:** One `npm exec` invocation of the pinned CLI package, with the same
  image-only prompt and strict JSON schema as A01. The candidate runs from
  `/tmp`, uses the read-only sandbox, and does not control a game or GUI.
- **D:** `PASS` requires a final schema-valid response with visible hostile=true,
  health 51, and ammo 38. A completed, valid response with any incorrect scored
  field is `FAIL`. Client/service rejection, malformed output, or incomplete
  raw evidence is `STOP`. No retries.
- **C:** A newer CLI may still be denied this model for the account. Even if the
  model responds, one screenshot cannot establish reliable recognition or a
  useful live action.
- **U:** One frame and one response do not establish live response, timely
  cancellation, key release, recovery, task effect, or MAP01 completion. The
  cover recommendation remains unscored and is never executed.

## Frozen provenance

The source is current main `6a2826d391b77496b69752609a6f07b6971b4b6f`.
`source.png` is the unchanged retained 1280×800 V39 sequence-200 PNG, SHA-256
`0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`. The prompt
and output schema are byte-identical to A01 and their hashes appear in
`freeze.json`. The official npm package reports version 0.160.0 and its frozen
integrity digest is recorded there. `run_once.py` writes an allocation sentinel
before the model request. Raw CLI output, first audit, result, and checksums
will remain in this additive package.

The successor is distinct from protocol-only PRs #7987 and #7996, which reused
the frame in loopback App Server tests without inference. PR #7995 preserves
A01's unsupported-model STOP. None of these protocol results is a vision result.

## Result

The single CLI 0.160.0 invocation returned a schema-valid message matching all
three scored fields. However, its JSONL also contains non-message error items:
the CLI reported an ignored user configuration key and MCP startup failures
for unrelated configured servers. The frozen tool/error policy therefore
dispositions the allocation as `STOP`; the compliant message does not override
that gate. The response's `STOP_OR_SWITCH` recommendation is retained but
unscored. No retry was made. A01 remains unchanged, and neither result tests
live behavior.

The initial `freeze.json` contained an accidental future `frozen_at_utc` value.
The pre-run bytes are retained as `freeze.pre-run.original.json`; the corrected
freeze records the file's pre-invocation mtime (05:09:21Z), before the candidate
start at 05:09:30Z, and documents the correction. Candidate asset hashes and
the recorded single invocation are unchanged.
