# State-preserving delayed writes

Research-only additive lane, Issue #332. Start with REPORT.md and CASE_TABLE.csv. This corrects a prior overgeneralization, not the immutable historical ref-replacement record.

Requirements: Python3.13.5 and Git2.47.3 on the measured Linux environment. No third-party Python dependencies. Repositories must be generated disposable fixtures, never user repositories. Complete raw evidence is a conversation attachment as specified in REPORT.md.

All four measured Python sources are byte-exact. `restore_plan.py` is publication-only convenience: it losslessly expands the recorded case order and checks the original premeasurement SHA256 before writing plan.json; it does not launch a job.

```sh
python restore_plan.py
python -m unittest -v test_contract
```

To audit retained evidence, extract the conversation archive into a new directory and run there:

```sh
python source/audit.py evidence source/plan.json replay.json
python source/review_history.py historical_input.tar.xz replay_history.json
```

These audit commands read the stored Git evidence; they do not reexecute scored cases. A fresh research/reproduction execution requires a separate allocation/output path and explicit new IDs, not replacing this dataset. The runner is `python experiment.py PLAN.json NEW_OUTPUT_DIR` and refuses an existing output directory. Original plan IDs and first outcomes must remain immutable.

The isolated-index candidate updates only effect.txt from the inspected current tree and publishes with current-OID CAS. A final write-target precondition rejects concurrent edits to that file. Read dependencies and the write scope remain authored; no production deployment or general GUI guarantee follows.
