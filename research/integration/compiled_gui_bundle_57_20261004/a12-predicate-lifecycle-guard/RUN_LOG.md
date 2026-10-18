# Run log

- Frozen checkout: `9fa379bb080f520f8f7d8080646857ca144243e7`.
- Candidate wrapper source: `candidate.py` (SHA recorded in `RAW.json`).
- Command: `python3 run.py > RAW.json`; exit 0.
- Command: `python3 audit.py RAW.json > AUDIT.json`; exit 0.
- Optimized audit: `python3 -O audit.py RAW.json`; byte-identical to `AUDIT.json`.
- Tamper control: removed the compiled action-branch `target_valid` count from a copied raw record; normal and optimized audits rejected it.
- No baseline R02 file was modified. No model/provider, GUI/input, container, or formal allocation ran.
