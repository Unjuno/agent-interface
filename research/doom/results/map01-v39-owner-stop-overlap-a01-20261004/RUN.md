# Run record

- Frozen main: `8094af4631fc7bc5d92990e5151d5e89477ee39f`.
- Frozen InputOwner v10 blob: `341b3c01649943ddaad5f28431a792c4889cc36e`.
- Candidate command: `python3 -B research/doom/results/map01-v39-owner-stop-overlap-a01-20261004/run.py` — exit 0; two deterministic cases saved.
- Independent audit command: `python3 -B research/doom/results/map01-v39-owner-stop-overlap-a01-20261004/audit.py` — exit 0; 18/18 checks.
- Package checksum command: from this directory, `shasum -a 256 -c SHA256SUMS.txt` — all nine listed files passed.
- `git diff --cached --check` — exit 0.

No X server, game, model, network, physical input, or formal allocation was
used. The two candidate cases are baseline and stop-overlap controls in one
construction run, not independent replications.
