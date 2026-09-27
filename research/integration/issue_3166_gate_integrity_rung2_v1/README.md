# Issue #3166 gate-integrity rung 2

This additive successor tests the held-out stale-dependency, malformed-receipt,
duplicate-commit, and collateral-effect cases omitted by rung1. Rung1 in
`issue_3166_fresh_gate_truth_v1/` and PR #4506 remains unchanged.

## Files

- `PREREG.md`: frozen H/T/D/C/U, 40-cell matrix, controls, and decision gates.
- `FREEZE.json`: main/source/image/runner/auditor/test hash pins.
- `policy.py`: experiment-only evidence comparators; not a production API.
- `run_formal.py`: one formal GTK/X11 allocation, writes JSONL and all fixture
  observations under `/evidence`.
- `audit_raw.py`: separate raw-only auditor; does not import the runner or
  comparator module.
- `results/formal-20260927-01/`: immutable 43-row allocation, raw GTK events,
  per-case effects, container/image identity, summary, audit, and checksums.
- `results/launch-stop-20260927-01/` and `LAUNCH_ERRATUM.md`: preserves the
  pre-formal Docker CLI syntax error and its syntax-only correction. The failed
  CLI invocation created no container and consumed no formal rows.

## Reproduce the formal container

Use the exact frozen source commit and cached image in `FREEZE.json`. The source
mount is read-only; the evidence mount is read/write (Docker's default when
`readonly` is omitted). The standalone corrected launcher is:

```sh
docker run --name issue3166-rung2-formal-20260927-01 \
  --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --cpus 2 --memory 2g --pids-limit 256 \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --mount type=bind,source=<checkout>,target=/repo,readonly \
  --mount type=bind,source=<fresh-empty-evidence-dir>,target=/evidence \
  --env FROZEN_SOURCE_COMMIT=2c5be06f9563deb3e5e739df6e7f154d145a8687 \
  --env FROZEN_IMAGE_ID=sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c \
  --workdir /repo --entrypoint /bin/sh agent-interface-2994:20260920 \
  -c 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/repo /usr/bin/python3 -B research/integration/issue_3166_gate_integrity_rung2_v1/run_formal.py'
```

Then run `audit_raw.py` in a distinct container with the repo mounted read-only
and the evidence mount writable only for `AUDIT.json`. Do not run the formal
allocation again; this exact allocation already completed once.

## Result

See `results/formal-20260927-01/REPORT.md` for the outcome and scope. The raw
two-tier matrix had zero invalid admissions, and reduced policies yielded
17 invalid exact GTK effects. The duplicate probe accepted the same program,
intent, epoch, and receipt twice, producing two save events. The independent
auditor found all 43 records and source hashes but also found cleanup failures
for every fixture because the pinned image lacks `xdotool`. Accordingly, keep
the duplicate replay as a directly observed FAIL finding while the overall
allocation disposition remains HOLD for cleanup/audit completeness. Issue
#3166 remains OPEN.
