# Retained edit-context dispatch-placement evidence (#4091)

This directory publishes an already completed local allocation. It is **retrospective evidence delivery**, not GitHub preregistration, and no consumed GUI/formal case was rerun for publication.

## Scoped result

`PASS_DISPATCH_PLACEMENT_BOUNDARY_SCOPED`.

| placement | cases | correct bounded append | refused Entry insertion | incorrect edit |
|---|---:|---:|---:|---:|
| HOST_ONLY | 12 | 4 | 0 | 8 |
| EVENT_EARLY | 12 | 4 | 4 | 4 |
| PRE_CLASS | 12 | 4 | 8 | 0 |

PRE_CLASS checks the same edit-context predicate after the controlled widget callback and immediately before ordinary Tk Entry insertion. Its eight refusals preserve an unresolved partial state; they are not repaired/completed tasks. Every formal case still emits, receives and releases the native `c` key. The refusal blocks application insertion, not OS emission.

See `REPORT.md` for H/T/D/C/U and limits. `REPORT.md`, `AUDIT.json` and `FREEZE.json` are byte-exact retained files.

## Formal review set

The publication reconstructs the complete formal raw/source denominator needed by the frozen raw-only auditor:

- a 244-file tar.xz capsule containing both 18-case formal batches, frozen sources, journals/effects/pixels/stdout/stderr, app/Xvfb exits, plan/environment/freeze/report/audit and unit tests;
- six byte-exact outer batch-launch receipts restored by `unpack_evidence.py`.

The capsule is 77,356 bytes, SHA256
`2e4321b2af1a48c6d4043545bdaa3749213f765772bf902020d764b37620634a`.
Seven binary parts are represented by eleven Base64 transport files; binary part 5 is subdivided because larger publication calls failed exact readback. `PUBLICATION_MANIFEST.json` binds every decoded part, every outer launch file and the final capsule.

Two oversized publication-only transfers were rejected and removed. A first publication manifest also contained incorrect per-part digest fields; the local restore gate rejected it before PR creation. Both incidents changed only delivery metadata. No experimental source/result changed and no formal case was rerun.

The original 402-member conversation/local bundle (construction plus predecessor history included) is recorded by hash but is not claimed GitHub-hosted by this PR.

## Read-only verification

Use a fresh destination:

```sh
python -B unpack_evidence.py /tmp/text-dispatch-4091
cd /tmp/text-dispatch-4091
python -B source/audit.py --root . --mode formal --controls
python -B source/test_gate.py
cmp AUDIT.json /tmp/text-dispatch-4091-audit.json  # if audit output was redirected here
```

For an explicit byte comparison:

```sh
python -B source/audit.py --root . --mode formal --controls > /tmp/text-dispatch-4091-audit.json
cmp AUDIT.json /tmp/text-dispatch-4091-audit.json
```

Do **not** rerun the consumed formal runner. The historical full-bundle retention verifier inside the capsule expects the unhosted 402-member full bundle and is not a review command for this reduced publication set.

This is research evidence only. It changes no shared runtime/default and establishes no arbitrary GUI atomicity, model/task benefit, performance gain, product readiness, or repository-wide roadmap completion.
