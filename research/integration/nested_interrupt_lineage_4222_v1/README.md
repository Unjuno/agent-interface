# Nested interrupt completion lineage — #4302

Result: **PASS_NESTED_INTERRUPT_LINEAGE_SCOPED**, 24 fresh private Tk/Xvfb sessions.
Start with [REPORT.md](REPORT.md), [PLAN.md](PLAN.md), and [CONSTRUCTION.md](CONSTRUCTION.md).

## Read-only reproduction

From this directory, with Python 3 standard library only:

```sh
python -B verify_publication.py
```

This verifies the 41,984-byte evidence archive, restores 193 exact files in a temporary directory, checks the public source freeze and original launcher receipts, reconstructs all 24 formal sessions with the frozen auditor, repeats the 12 evidence-corruption controls, and runs eight I/O-free policy tests. The reconstructed audit and controls must be byte-identical to the retained first results. It does not invoke `run.py`, create a display, or issue task input.

All raw application journals, controller rows, source copies, construction attempts and process receipts are retained losslessly in `capsule/part-*.b64`; `EVIDENCE_MANIFEST.json` binds the exact parts and compressed archive. Plain source and result files remain directly readable. Xauthority cookies and Python caches are not evidence and are not published.

## Integration boundary

`policy.Continuation.deliver` matches completion to the current top frame by exact session, interrupt ID, generation and parent. Its output grants eligibility only. Preserve #4222's current task, pending-result, source, queue and target checks before consequential input. Missing child completion stays unresolved; do not infer task success from window closure.

The weak comparator is a directed diagnostic, not the deployed runtime. The separate audit code was authored in the same session, not an independent reviewer. No model, token/latency, arbitrary-depth, authentication, cross-platform or production claim follows. Global ROADMAP/#57/#2789 remain open.
