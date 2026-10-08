# A09 live result and audit reconciliation

Allocation `map01-v39-live-threat-guard-a09-20261009` ran once on exact main
`ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`, using experiment-tree commit
`a5fe0fe4378535894a352af13ed518e47c4c9e06`. The original output and original
`AUDIT.json` remain unchanged under `results-local/doom/`.

The isolated guest and app-server both exited 0 after 58.468 seconds. The run
completed all 10 model decisions and reached the preregistered health guard:
typed health fell from 100 to 88 against a bound of 90 while inference was
pending. The matching planner turn was interrupted and marked ineligible; its
dependent answer was discarded. A newer observation was used for recovery at
the next decision. The guard's `cover-2` cancellation has a matching
same-token owner release with verified empty keys/buttons/unknown state. All 21
accepted programs have terminals, and each terminal reports verified empty
input. Ten local-image requests have ten matching host SHA-256 receipts.

The frozen auditor reports `FAIL` because it requires a separate
`input_released` event for every matched `cancel_requested` ID. Four cancel
records (`cover-0`, `cover-1`, `cover-3`, `cover-4`) have no interruption lease
token or separate input-release event; their matching cancelled terminals
contain verified-empty releases. The actual hard-health cancellation (`cover-2`)
does have the explicit release event and matching lease token. The original
`AUDIT.json` and its result are preserved; this correction does not rewrite or
silently relabel it.

The complete raw output tree is published in `A09_RAW_SANITIZED.tar.gz`:
2,258 files / 104,964,572 original bytes. The archive carries both local-original
and public-copy SHA-256 manifests. Its text records replace only the host
checkout and home path literals; PNG/AIT bytes and all other record content are
preserved. The compressed archive SHA-256 is
`90f9c89728dd7509d6a8a8e97895475c65620a391be291c77e0da59cb4ed3b47`.

The additive `audit_live_reconciliation.py` applies that distinction and
fails closed when an interrupted lease lacks a matching token-bound empty
release. It independently classifies the raw cancellation custody as sound
for this allocation. The experiment's preregistered full gate is still
**HOLD**: one useful kill-count event occurred outside model wait, and zero
useful scorer events occurred while a model turn was pending. Final score was
2 kills, 0 deaths, no MAP01 exit. No task-completion, survival-benefit,
latency-benefit, or generality claim follows.

## Verification

- The original frozen auditor was run once and retained as `FAIL`.
- Public raw archive: all 2,258 file hashes and content transformations verified;
  no host-home path literals remain.
- Cancellation-reconciliation tests: 3/3 pass, including controls for missing
  active-lease release evidence and empty no-lease terminal receipts.
- Supplemental raw-event reconciliation: 10/10 matched cancellations resolve
  to verified-empty terminal custody; the guard cancellation has its explicit
  same-token release. Classification: `HOLD` because pending-model useful
  feedback was not observed.
- The experiment allocation was not retried. No game or model was run during
  this audit correction.
