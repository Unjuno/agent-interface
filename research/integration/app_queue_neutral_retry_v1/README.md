# Delayed application consumption after neutral input

Issue #3945; see [REPORT.md](REPORT.md) for H/T/D/C/U, first outcomes, failures,
limits and the integration handoff. The frozen private Tk/Xvfb experiment found
that a neutral server and current zero effects can coexist with an eventual
queued effect; blind retry doubled that effect in all three control sessions.
No production runtime or predecessor evidence is changed.

The lossless capsule in `parts/00.b64` through `parts/04.b64` contains complete frozen Python sources,
environment/plan/freeze, construction STOP and successful construction evidence,
all original formal per-case files, raw JSON, execution receipts and audits.
Encoding is used only to retain exact evidence bytes through the text-only MCP
write path. Extraction never executes the experiment. Inspect the unpacked
source before running any code.

Read-only reproduction of the **audit**, not a rerun of the formal experiment:

```sh
python unpack.py /tmp/issue3945-audit-copy
python -B /tmp/issue3945-audit-copy/audit.py /tmp/issue3945-audit-copy/formal-01
```

Use a new empty/nonexistent destination. The unpacker verifies the capsule hash,
rejects links/path traversal/oversized members, and verifies every manifest
entry. The raw-only auditor uses the Python standard library, not Tk/Xlib.
Its expected result is PASS_APP_QUEUE_NEUTRAL_BOUNDARY_SCOPED, 15 rows, no errors,
and 12 rejected corruption controls. PACKAGING_VALIDATION.json records the
actual extraction/re-audit performed on the local publication bytes.

Do **not** rerun `run.py --mode formal`, run `prepare_freeze.py`, overwrite any
formal path, or count restored evidence as a second experiment. A live successor
requires a separately preregistered identity/environment and fresh output path.
The capsule is a research deliverable, not a dependency of production code.
