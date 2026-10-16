# A04 — versioned trace sample audit

This package attempted one raw-only audit of retained A02 fake-X output. Its auditor verified named pre/post query-to-result binding and included 12 mutation controls. The one formal run terminated before parsing because the input hash map referenced undefined `pre_run`; see `RUN_RECORD.md` and `DISPOSITION.json`. Candidate invocations: 0; auditor invocations: 1; retries: 0. A04 is terminal and must not be retried.
