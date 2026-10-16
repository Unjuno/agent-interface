# A07 saved-trace audit-v3 addendum

This is an additive read-only reconciliation of the retained A07 episode. It
does not replace `AUDIT.json`, `AUDIT_V2.json`, or the preregistered HOLD.

## Inputs and custody

- Source auditor: `audit_live_v3.py` from PR source commit
  `6e308de606ef684ee07406b40958c3275c0bc7aa`, SHA-256
  `8784e0e2cbf4148aeb88562a200ff8979324b749dceaf6a73d7e27524fbcc09e`.
- Local ignored A07 output manifest: 2,358 entries, all byte counts and hashes
  matched; manifest SHA-256
  `a7ed0abe21ad1571131511abfb1b248a61ed5d13e7eaafd196caf2a741ef5844`.
- The auditor ran against temporary copies of `AUDIT.json`, `AUDIT_V2.json`,
  `episode/report.json`, `episode/runtime/events.jsonl`, and
  `episode/runtime/score.json`. The output below was saved separately; the
  original ignored output directory and its audits were not written.

## Result

`A07_SAVED_TRACE_AUDIT_V3.json` records `status=FAIL`, `scoped_pass=false`, and
`formal_pass=false`. There are 10 unique, matched cancellation IDs and no
post-cancel admissions. Four cancellations have no input admission or release
transition. Six have admissions: `cover-1`, `cover-2`, `cover-3`, `cover-4`,
`cover-5`, and `cover-8`. Five of those six have one fewer release-transition
row than admission rows (three are 6/5 and two are 4/3); `cover-3` is 4/4.
The five unmatched per-key counts make v3's custody check fail.

## Additive terminal-release reconciliation

The independent check in `audit_a07_owner_release_reconciliation.py` joins
`input_admission` to the same-key `keys_held` acknowledgement, matches every
`input_release_transition` to an owner-thread explicit key-up, and uses the
terminal owner-release receipt for a key that was still held when cancellation
arrived. All 10 cancellation rows reconcile. Four have no admission, held-key
acknowledgement, transition, or input-release receipt. For the six admitted
rows, all admissions match held-key acknowledgements; five have one additional
terminal key-up receipt (three `a`, two `d`) corresponding to the one fewer
explicit transition in v3. Each receipt reports the key down before and up
after, a completed sync, a verified keycode entry, and an empty final server
key state. The remaining admitted row has one explicit transition per key.
The five unit regressions pass, including missing-terminal-keyup,
post-cancel-admission, and duplicate-ID rejection.

The supplemental JSON therefore records
`PASS_CUSTODY_RECONCILED_SCOPED`. It explains why v3's stricter explicit-row
count fails without erasing that v3 `FAIL` or changing either earlier audit.
This remains X11 server-side custody evidence, not physical-key or game
consumption evidence. A07's overall result remains HOLD because the live
episode did not expose the preregistered health-guard/useful-feedback condition
or complete MAP01. Do not rerun the allocation.
