# Reproduction

Run:

```text
python experiment.py
python audit.py
python corruption_controls.py
```

Expected candidate summary: 256 rows, 16 valid, 240 rejected, SHA-256 `5c2699e993fd163a1a01c72c3905b46c8f364e329a8ddef47c37bb713952b936`.

Expected independent audit: 256 rows, 16 valid, 240 rejected, `PASS`.

The local Docker reproduction is recorded as PASS with the scope boundary in `MANIFEST.json`.
