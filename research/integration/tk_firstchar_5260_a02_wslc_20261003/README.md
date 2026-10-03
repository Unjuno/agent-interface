# #5260 A02 WSLc first-character diagnostic

Overall STOP_READINESS_CUSTODY_AFTER_PASS_AUDIT: 65 exact saves/31 nonexact
are descriptive; frozen auditor PASS_AUDIT/errors[], stronger checker failed
all96 readiness epoch bindings. Read [REPORT.md](REPORT.md), then
[PREREG.md](PREREG.md), [FREEZE.json](FREEZE.json), and [LEDGER.md](LEDGER.md).
The old r0 STOP and dormant A01 proposal are not altered or reallocated.

Local image build, both construction inputs and the failed first auditor
are retained under `construction/`. Smoke02 observed h delivered to decoy
before target FocusIn, target saved xy. Construction is not formal evidence.
Intermediate smoke01 runner/auditor variants were not committed separately;
their exact runtime outputs/argv/image remain, but current source is not
asserted to reconstruct every intermediate variant byte-for-byte.

Formal commands: `python -B host_capture.py --frozen candidate`, then
`--frozen auditor`. They require a clean frozen branch, verify source hashes,
and refuse occupied receipt or data directories. Only the owner allocation
may invoke them. CI must run retained-only validation, never these commands.

Seventeen local tests passed before freeze; six additional retained-custody
tests plus explicit STOP-preservation gate passed after outcome (24 total).
Built image uses Debian Python
3.13.5/Tk 8.6 on WSL2 amd64. CPU/memory flags are requests, not effective-cap
or migration-benefit evidence. First-frame OCR remains exploratory.
