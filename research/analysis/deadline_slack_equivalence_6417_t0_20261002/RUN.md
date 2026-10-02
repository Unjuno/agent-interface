# Run record

- **Base:** `8115db8f493b6c13db7e6319ff751a23c77729fc`; branch `research/deadline-slack-equivalence-6417-t0-20261002`.
- **Preformal construction:** initial `test_slack_sensitive_control_switches_and_impossible_case_yields` caught a positive-control arithmetic error: the supposedly excluded route still fit the short deadline. The case was corrected before freeze; all three construction tests then passed. No candidate/auditor had run at that point.
- **Runtime preflight:** 2026-10-02, macOS arm64. Neither `wslc.exe` nor `wslc` was present. Docker context read as `orbstack`; no Docker/OrbStack engine command was invoked. No image/container claims are made.
- **Freeze:** see `FREEZE.json` for exact base, candidate/auditor invocation limits, thresholds, tie-break, runtime deviation and source hashes.
- **Formal candidate command:** `python3 research/analysis/deadline_slack_equivalence_6417_t0_20261002/candidate.py`; exit 0, exactly once. `candidate.raw.json`, `candidate.stdout.json`, `candidate.stderr.txt`, `candidate.exit.txt` retained.
- **Formal auditor command:** `python3 research/analysis/deadline_slack_equivalence_6417_t0_20261002/audit.py`; executed only after candidate exit 0; exit 0, exactly once. It does not import candidate. `audit.raw.json`, `audit.stdout.json`, `audit.stderr.txt`, `audit.exit.txt` retained.
- **Postrun:** no candidate/auditor retry, correction, seed search or pooling. Remaining repo delivery checks are separate from the formal T0.
- **Excluded:** model, human, GUI, GPU, network, shared container engine, live approval, external effect and user data.
