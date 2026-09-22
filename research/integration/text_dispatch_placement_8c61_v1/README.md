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

See `REPORT.md` for H/T/D/C/U and limits. `REPORT.md` and `AUDIT.json` are byte-exact copies of the retained local files; `FREEZE.json` retains the local preformal source/gate hashes.

## Formal evidence capsule

The complete formal denominator and frozen sources are retained losslessly in a 244-file tar.xz capsule:

- 36 formal app cases in two immutable batches;
- all source files used by the formal run;
- raw journals/effect snapshots/pixels/stdout/stderr;
- actual app/Xvfb/batch/supervisor exits;
- PLAN, INTAKE, ENVIRONMENT, FREEZE, REPORT and AUDIT;
- retention verifier and unit tests.

The 77,356-byte capsule SHA256 is
`2e4321b2af1a48c6d4043545bdaa3749213f765772bf902020d764b37620634a`.
It is represented as seven binary parts. Because one publication call could not safely carry the fifth Base64 string, binary part 5 is itself represented by five smaller text files. `PUBLICATION_MANIFEST.json` binds every decoded part and the final capsule.

Two oversized publication-only transfer attempts failed exact readback and were removed. No scientific source/result changed and no formal case was rerun.

The original 402-member conversation/local bundle is recorded by hash in the manifest but is not claimed GitHub-hosted by this PR; construction and predecessor-history details remain truthfully documented in the report.

## Read-only verification

Use a fresh destination:

```sh
python -B unpack_evidence.py /tmp/text-dispatch-4091
cd /tmp/text-dispatch-4091
python -B verify_retention.py
python -B source/audit.py --root . --mode formal --controls
python -B source/test_gate.py
```

Do **not** rerun the consumed formal runner.

This is research evidence only. It changes no shared runtime/default and establishes no arbitrary GUI atomicity, model/task benefit, performance gain, product readiness, or repository-wide roadmap completion.
