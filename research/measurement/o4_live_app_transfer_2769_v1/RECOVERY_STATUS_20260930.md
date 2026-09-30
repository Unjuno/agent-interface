# Issue #2769 remote-branch recovery status

This file records a partial archival recovery only. It does not promote the
reported experiment to a fully reproducible result.

## Preserved, unchanged

The old branch's report, freeze, schedule, source, auditors, corruption
controls, publication notes, and its sole committed evidence part are copied
without editing. The formal allocation is consumed; no rerun is authorized.

## Publication boundary

- `PUBLICATION.json` declares a 15,684-byte archive with SHA-256
  `33f01182dbe3e26266f8296432e849cbcec9f94464683b0a8995b366d651289d`,
  64 archive members, and a complete Base64 SHA-256
  `a0d77f6344678bf00b5acf44a3c4f0a23ea4c3bd93ff0aa74f2fd4b7c93edaaf`.
- Only `EVIDENCE.part00.b64` is present. Its exact 3,000 bytes decode to 2,250
  bytes (decoded SHA-256
  `bb832dbe8043b3711baf8a8047e0f37f813e0b3ebf9a199f9bb846aa4a77c8dc`),
  which cannot reconstruct or verify the declared full archive. The reported
  `PASS_RAW_AUDIT` is therefore not independently reproducible from this
  committed partial archive.
- The frozen corruption-control outcome is 7/8, below the required 8/8.
  `controls_v2.py`'s postformal 8/8 is diagnostic only and does not override
  the frozen first outcome. The canonical `REPORT.md` disposition remains
  `HOLD_FROZEN_CORRUPTION_CONTROL_INCOMPLETE`; the `FREEZE.json` pass field is
  not an overall disposition and does not waive that failed gate.
- The committed public `PLAN.md` hash differs from the frozen local PLAN hash.
  The separately retained `PLAN_EXECUTED_LOCAL.md` matches the declared
  SHA-256 `5fbe167e91889aefa5dd18ea50f97fb67132222992621103189ff0cc84ca384d`.
  Both historical texts are kept unchanged; see
  `PUBLICATION_DISCREPANCY.md`.

## Recovery checks and limits

On 2026-09-30, read-only checks confirmed the exact part00 byte count/hash,
decoded count/hash, and all six frozen source identities except the explicitly
documented public PLAN discrepancy (the local PLAN copy matches). The four
Python programs pass syntax compilation, and committed JSON files parse.
No formal runner, raw auditor, corruption-control command, GUI/Xvfb, Docker,
model/provider, network experiment, or user-desktop input was started in this
recovery because the declared raw archive is incomplete and the allocation is
already consumed.

This partial record is retained on `main` solely so later workers can find the
exact historical HOLD and remaining delivery boundary. Issue #2769 stays open
for the missing original bytes and any separately justified successor. Do not
pool related allocations, infer a complete audit from the Issue summary, or
delete/replace the missing data by regenerating it.
