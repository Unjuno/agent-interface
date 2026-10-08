# Run record

- Allocation: `RECEIVER-SYNTHESIS-6112-T0-20261002-01`
- Freeze: `FREEZE.json`; source and input hashes are in `SHA256SUMS`.
- Construction checks, before freeze: `python -m unittest discover -s . -p 'test_*.py' -v` — 4/4 pass.
- Official candidate run, once after freeze: `python runner.py` — 9 fixed response rows; raw output retained in `FORMAL.json`.
- Independent audit, once: `python audit.py` — 9/9 decisions and correction-field requests match; raw audit summary retained in `AUDIT.json`.
- Formal candidate retries: 0. Human participants: 0. Candidate runner opened oracle truth: false.
- No Docker/live GUI/model/input execution; exact synthetic protocol validation is platform-independent. Docker Desktop Engine CLI probes did not return within 10 seconds.
