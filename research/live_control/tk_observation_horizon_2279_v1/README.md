# Observation deadline validation (#2279)

Read REPORT.md for the first 24-case result and PLAN.md for the unchanged
premeasurement H/T/D/C/U, proof and scope. Frozen sources are directly readable.
No shared runtime or historical result is changed. #2279 remains open.

## Re-audit only — do not rerun the consumed experiment

From this directory, with an absent destination:

```sh
python -B unpack.py /tmp/tk-horizon-evidence-2279
python -B audit.py /tmp/tk-horizon-evidence-2279/formal 0 1 > /tmp/tk-horizon-audit.json
cmp /tmp/tk-horizon-evidence-2279/formal/AUDIT.json /tmp/tk-horizon-audit.json
python -B -m unittest -v test_source
```

The raw audit requires Python standard library only; it imports no Tk/runner.
The source-shape unit test imports worker.py and therefore requires tkinter,
but creates no GUI or model. Do not use Python -O (auditor assertions must stay
active). `run.py` and `worker.py` are consumed experiment sources, not automatic
reproduction commands. A new allocation needs a justified new prospective plan.

EVIDENCE.json binds six lossless XZ/base64 parts, the complete30-file evidence
inventory, expanded bytes and each member hash. `unpack.py` checks every byte
before writing an absent output directory, bounds decoding and executes no
experiment. The payload includes all12 construction and24 formal protocol rows,
original stdout/stderr/exit records, terminal receipts and unchanged audits.
Hashes provide integrity, not authenticity. PUBLICATION_CHECK.json records
fresh restoration and read-only revalidation; CI/merge status is separate.
