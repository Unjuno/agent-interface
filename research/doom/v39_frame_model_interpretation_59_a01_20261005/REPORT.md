# Issue #59 A01 — saved-frame model interpretation STOP

## Question and frozen test

This probe asked whether the selected Codex model could read the visible threat
and HUD values in V39's retained sequence-200 screenshot, then give an
unexecuted recommendation about the bounded cover program in progress. The
question was intentionally narrower than the open #59 live gate: this did not
test observation delivery, whether current evidence interrupts an active
cover, per-key release, recovery, or game outcome.

The freeze is `freeze.json` (SHA-256 `895e16be1d146abd205e77a0be020000a5d0a6cae62f8c316d75223e97b8f846`). It binds source main
`6860b585305e539ec93896f5adcbf658cbbd8592`, the retained 1280×800 PNG
(`0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`), its
sequence-200 source records, prompt, strict JSON schema, one-shot runner, and
independent auditor. Before the candidate invocation, the expected visible
hostile flag and typed HUD reference (health 51, ammo 38) and all gates were
fixed. The recommendation was unscored and could not cause an action.

## First outcome

The candidate was invoked exactly once with Codex CLI 0.146.1, requested model
`gpt-6.1-sol`, and medium reasoning effort. The process exited 1 and produced no
final response. The CLI event stream and stderr preserve the service rejection:

> HTTP 400: The `gpt-6.1-sol` model is not supported when using Codex with a ChatGPT account.

The CLI also reported missing model metadata and selected fallback metadata;
therefore the model identity was never accepted for this run. No screenshot
comprehension result exists. The independent deterministic audit returned
`STOP`; it verified the PNG, frozen prompt, source records, requested arguments,
and recorded exit status. Its non-message event list contains CLI `error`
items, not model-generated tool executions. Candidate retries: zero.

The original event JSONL, stderr, invocation arguments/timestamps, source event
records, and audit output were preserved locally in `raw/private-local/` with
directory mode 0700 and file mode 0600; their SHA-256 values are in
`REDACTIONS.json`. The public copies redact the ephemeral thread ID and local
home/worktree/runner-image paths. The original A01 audit is unchanged. The
first redacted-copy audit construction error and its 9/12 FAIL are retained;
`audit_redacted_v4.py` then passed 12/12 custody/redaction checks without
rerunning A01. The stdin prompt and exit code remain in `raw/`. This is a local
client/model-availability STOP, not a model-vision FAIL or PASS. The consumed
A01 allocation remains immutable.

## H/T/D/C/U disposition

- **H:** Not evaluated. The model request was rejected before any model
  response.
- **T:** One non-interactive CLI invocation with one retained image; no game,
  GUI, or controller operation.
- **D:** The predeclared result is `STOP` because model/service setup failed and
  no response or inference result was produced. The audit agrees.
- **C:** CLI version/account model restrictions prevented this method from
  testing visual interpretation; they say nothing about whether Sol 6.1 can
  recognize the screenshot in a supported client.
- **U:** This result does not answer whether the model sees the enemy or reads
  health/ammo, and does not test immediate response, action release, recovery,
  task effect, latency, or MAP01 completion. The #59 private live-game lane
  remains unassigned.

## Integration boundary

This package is additive, offline evidence. It is distinct from open PR #7950's
synthetic frame-identity/API boundary and PR #7913's frame-color/typed-health
boundary studies; neither invoked a model on this retained image. PR #7987,
opened after this allocation, uses the same sequence-200 image for a loopback
`turn/steer` protocol test but explicitly runs no inference. No V39 runtime code
changed. A future inference test requires a separately frozen allocation using
a client/account combination that explicitly supports the designated model.
Do not rerun A01 or relabel this STOP as a model result.
