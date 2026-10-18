# Issue #5905 A07 — candidate launch STOP

The raw-only blinded comparison never evaluated because the formal candidate invocation mounted `observations/` at `/input/observations` while it passed `/input` as its root; the frozen program expected `/input/manifest.json`. The container exited with `FileNotFoundError` before reading any sequence. Candidate invocations=1, auditor invocations=0, retries=0. Disposition: `STOP_CANDIDATE_INPUT_MOUNT_PATH_ERROR`; scientific result: `NOT_EVALUATED`. The A07 allocation is consumed and will not be restarted.

A separate network-disabled WSLc builder had already generated a fresh 30-case corpus and assigned shuffled opaque IDs `item_00`…`item_29`; the candidate-visible manifest SHA-256 is `50ba620397cfd327792eab32e96f3ba2877cefe67556e6ad6fbcbd77a0aefd2a`, while sealed-truth SHA-256 is `fa1c660491201a0cdcf544e66a00b6c01ef1b08e291dbffad459319c395fffc0`. Candidate and auditor source were byte-identical to the methods frozen from A06; generator and all identities are in `FREEZE.json`.

This STOP tests no scientific outcome and says nothing about TTC versus the baselines. It does not meet #59's live threat-exposure, useful-feedback, recovery, or task-outcome gate. Any corrected follow-up requires a separate successor allocation, a fresh exact-main freeze and a corrected mount contract. All A02–A06 records remain unchanged.

