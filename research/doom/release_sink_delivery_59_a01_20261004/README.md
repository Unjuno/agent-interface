# Release sink delivery-boundary probe (Issue #59, A01)

## H / T / D / C / U

**H:** The current owner-thread release-batch publisher removes each row from its pending list before calling the telemetry sink. If the sink raises, a row rejected before acceptance is lost from later incomplete-batch reporting; if the sink accepted then raised, the row is externally present but still has no explicit `delivery_unknown` marker.

**T:** At frozen main `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`, inject one sink exception at each of three batch positions, in two modes: fail before acceptance and accept-then-raise. Preserve the candidate source unchanged. Classify each row's observed presence and completeness; no retry is allowed.

**D:** All 3/3 fail-before-accept positions disappear from observed output. In all 3/3 accept-then-raise cases the row appears as `release_batch_complete=True`, with no `delivery_unknown` status. Later rows, when any, are published as incomplete. Independent raw audit passes these classifications. The probe therefore supports the stated evidence-custody bug and narrows the repair to position-aware batch status carried beyond the failing sink call; it does not choose a safe retry policy.

**C:** Deterministic synthetic sink and stub owner state; invokes the exact `_publish_release_batch` implementation loaded from the frozen Git object. No X server, game, model, GUI, OS input or live allocation. Host: Ubuntu WSL2 Python (local process), not Docker/WSLc. Docker CLI is present in WSL, but its daemon socket is absent; `wslc` is unavailable. This is a construction boundary experiment, not physical-release or gameplay evidence.

**U:** Whether a future terminal/report sink can durably carry a per-position `delivery_unknown` ledger without re-entering the failed sink remains untested. Also unknown: real filesystem/pipe sink behavior, consumer reconciliation, application receipt, physical release and task effect.

## Frozen source and reproduction

- Commit: `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`
- Path: `research/doom/doom_owner_thread_release_batch_backend_v1.py`
- Git blob: `93be5c2d05d946d43a7f063008e591dd66de2779`
- SHA-256: `a9e109f07dbfdefbf33e87840528c4e24195b2d435782d92f0880049721d0b7d`

From a full clone that contains the frozen commit, run:

```sh
python3 probe.py /path/to/agent-interface
python3 audit.py
```

`RAW_STDOUT.txt` is the captured output of the exact probe command. The auditor reads only that retained output and checks all six cases; it does not rerun or modify the candidate. No source change is proposed in this package.
