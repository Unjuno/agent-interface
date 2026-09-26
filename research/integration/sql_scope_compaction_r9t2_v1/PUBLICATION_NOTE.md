# Retrospective publication note — 2026-09-26

This directory publishes the already-completed local allocation
`sql-scope-compaction-20260926-r9t2-01` under Issue #4429.

The original REPORT/README in the evidence archive remain historically unchanged,
including their statement that GitHub write operations were unavailable in the
execution connection. This later publication does not convert the local source
freeze into public preregistration and does not rerun the scientific allocation.

Original allocation facts:
- formal cases: 48; formal reruns/replacements/exclusions: 0;
- decision: `PASS_LOCAL_SCOPE_COMPACTION_BOUNDARY`;
- unconditional `SCOPE_ONLY` adoption is rejected because writer-profile OFF
  produced four stale stored query results;
- frozen source SHA-256: `31207f53e0fe5b76c01f55513fecf45f52af8fc9e1c8a9815b6daa3f9e731138`;
- raw manifest SHA-256: `51c98e04b373fd2c3eb3311753af4d09e8b707e06b46bee67548ad63b8fb2481`;
- audit SHA-256: `974cc199474c738152d35b672a807ba9d4ce11f84a77ceb0b3157441b7271cc0`.

`EVIDENCE.tar.xz` is a lossless archive of all 588 original study files.
`CAPSULE.json` binds its bytes/counts. `verify_capsule.py` checks the archive
before extracting to a new destination; it does not invoke scientific actors or
consumed formal batches.

This publication changes no shared runtime/workflow/root direction file and does
not close #1713/#57/#2789 or the global ROADMAP. Active #4394 tests a different
boundary: trigger-maintenance lifetime across DDL; preserve it unchanged.
