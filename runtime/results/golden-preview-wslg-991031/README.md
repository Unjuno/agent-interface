# Frozen WSLg golden desktop preview — allocation 991031

This is one fresh, no-retry persistent-only acceptance run against the v2 runtime-preview source SHA `fc38624476aa1f30c381e5932f383224451a7d63` (inner artifact tar SHA-256 `abfdd71990b5c8608ddfe329a205a56ed19bf4a79255d11e2fd93a159ca04ece`). It is a release-host mechanics/correctness check, not a matched efficiency experiment.

## Preregistered design

H/T/D/C/U was registered before the run in [Issue #58](https://github.com/Unjuno/agent-interface/issues/58#issuecomment-5863657614). The unique six-task allocation used seed 991031 and output path `artifacts-local/golden-desktop-preview-wslg-20260928-01`; prior seed 991030 was not repeated.

Frozen Git checkout preflight passed in committed-Git-and-filesystem mode. Both launchers were committed as mode 100755 with matching bytes. Networked setup installed all nine exact pins. The WSLg doctor passed 15/15 checks; the retained benchmark audit passed with no source mismatches. No matching recovery/golden/app-server process was active immediately before registration/run.

## Result

The runner report and immediately following independent `audit-live` both passed:

- exact tasks: 6/6;
- planner generations including schema/grounding preflight: 3;
- model-visible images: 2;
- input usage: 29,427 total input tokens (8,960 cached), 439 output tokens (96 reasoning);
- stale old-layout reference checks: 1; old-target pointer admissions: 0;
- bounded repair: succeeded;
- terminal programs/releases: 57/57 verified;
- six-task elapsed: 46.732 s; whole command: 60.848 s.

This is one run only. It does not establish a population success rate, broad GUI reliability, a matched efficiency/token comparison, human-level speed, or DOOM success.

## Retained evidence and replay

`raw.tar.gz` (42,229 bytes, SHA-256 `5ecb7ae9e4b9d555759f151022643330ccd66605b1d1dff13d794146e079c9ee`) contains the report and the minimum raw gate/runtime records required for offline `audit-live`. Its manifest gives byte counts and SHA-256 for each member. Two local identifiers are redacted: the Codex grounding thread ID in the report and its matching preflight `thread.started` ID. The full Codex protocol transcript and high-volume journal are intentionally excluded; neither is needed by the independent audit. Original unredacted report/audit/doctor/log hashes are in `audit-summary.json`.

To replay the read-only audit using the frozen source checkout, extract `raw.tar.gz` to a dedicated directory and run from the checkout:

```bash
./runtime/golden-demo-v3.sh audit-live /path/to/extracted-evidence
```

The original smoke, setup, doctor, retained-audit, run and live-audit outcomes are recorded in `allocation.json` and `audit-summary.json`. The orchestration wrapper captured the passing runner JSON as stdout and empty stderr, but did not retain a separately parseable numeric child exit code; therefore the recorded success is grounded in the runner's `passed: true` report and the independent live audit, not a claimed shell exit value.
