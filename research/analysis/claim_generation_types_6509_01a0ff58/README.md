# Retained caller-generation argument boundary (#6509)

Read [REPORT.md](REPORT.md) for the four first outcomes and limits; [PLAN.md](PLAN.md) and [FREEZE.json](FREEZE.json) preceded the boundary. [SOURCE_PINS.json](SOURCE_PINS.json) ties the exact legacy source, contract and retained c03 input to actual Git blobs. [results/raw.json](results/raw.json), [results/AUDIT.json](results/AUDIT.json) and [results/BOUNDARY.json](results/BOUNDARY.json) preserve the first result and separate raw-only audit.

All evaluated/auditor source is inert `.py.txt`, with no package initializer, test-discovery name, import/default/distribution/workflow integration. The raw-only audit can be explicitly executed from this archive with `python -B audit.py.txt`; it does not call either reader. Do not replay `probe.py.txt` or the old writer/process matrix to validate preservation. `SHA256SUMS` covers every packet file except itself. No runtime adoption or permission is implied by a COMPLETE label.
