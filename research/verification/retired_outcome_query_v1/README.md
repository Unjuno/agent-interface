# Retired outcome-query coverage — Issue #4027

**Research evidence only.** Read REPORT.md for the first formal result and
PLAN.md for H/T/D/C/U, exact scenarios, fields/units and scope. The intentionally
unprotected receiver is a comparison fixture, not a production guard.

One source-first allocation: 48 fresh private SQLite cases, three supervised
batches. Lookup-only creates three duplicate and three conflicting extra old-ID
effects. Coverage-aware creates none, while conservatively leaving three
never-submitted old requests unresolved. New independent work remains usable.
A null result outside retained coverage proves neither failure nor completion.

All frozen Python sources are directly readable here. The seven binary parts
are one lossless, SHA-256-bound 38,900-byte tar.xz, not seven separate formats.
PACK.json describes their exact order and hashes. They preserve all 173 original
source/evidence files, including raw database bytes, SQL/IPC/process receipts,
excluded construction and its original failed auditor. Unpacker validates and
writes files only; it starts no subprocess, allocation, GUI or model.

## Read-only reproduction

Use Python 3.13 with SQLite deserialize support, standard library only, and an
absent absolute output path. From this directory:

```sh
python -B unpack.py /tmp/issue4027-audit
cd /tmp/issue4027-audit
sha256sum -c SHA256SUMS
python -B audit.py formal-01 --controls > /tmp/issue4027-audit-output.json
cmp AUDIT.json /tmp/issue4027-audit-output.json
python -B -m unittest -v test_policy
```

Do not execute the consumed formal run.py/supervise.py allocation or edit its
FREEZE.json. Postformal read-only verification is not a new experiment. The
original failed construction audit remains failed; it is not replaced by v2.

Provided Linux x86_64 execution container, Python3.13.5, SQLite3.46.1. No
Docker/OrbStack image-attestation, model/GUI usefulness, external-effect
atomicity, natural failure frequency, performance or exactly-once guarantee.
Separate auditor code/process is not external human review. Publication and
main/CI disposition are recorded in the Issue/PR, not inferred from local PASS.

Shared runtime, historical results and parallel-worker paths are unchanged.
#2084/#331/#2789 and the repository roadmap remain open.
