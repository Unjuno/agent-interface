# Passive reader: in-band producer epochs

Issue #3933; bounded successor to #3876 and closed #742. See REPORT.md for the
48-case result and PLAN.md for the predeclared H/T/D/C/U and matrix. This folder
is additive research evidence only. Existing reader/ledger/runtime are unchanged.

## Inspect retained evidence without rerunning the experiment

From this directory, with Python 3.13 and the standard library:

```sh
python unpack_evidence.py /tmp/epoch3933-evidence-new
python audit.py /tmp/epoch3933-evidence-new/epoch-formal-20260922-01/RAW.json \
  --expected-sha256 103bf32ca14d060edc80f18c52caf337c4b0d69cdcc9e86bc99e6249305349c2
EPOCH_CONSTRUCTION_RAW=/tmp/epoch3933-evidence-new/epoch-formal-20260922-01/RAW.json \
  python test_study.py
```

Use a new destination: unpacking refuses to overwrite one. It verifies every
part, the xz bytes and the decoded payload before writing any evidence file.
No network or external dependency is required. Source integrity is checked by
the auditor against FREEZE.json. The test command performs only gate/unit and
raw-mutation checks, not another 48-case producer/reader allocation.

`evidence/MANIFEST.json` binds four textual base64 parts containing a lossless
xz-compressed JSON map of 189 UTF-8 files. These include the exact original
formal RAW.json and per-case snapshots/files, every process request/response and
exit receipt, initial audit/controls/stdout/stderr, construction-01 partials and
source preimages, and all construction-02 evidence. The readable AUDIT.json,
MUTATIONS.json and DRIVER.json are exact copies of the first formal receipts.

The original formal launch was `python orchestrate.py formal
epoch-formal-20260922-01`. Do not rerun or replace that allocation. A new
experimental replication requires a distinct provenance/allocation and should
remain separate from the retained outcome. This experiment used the provided
Linux execution container; Docker/OrbStack engines were unavailable.
