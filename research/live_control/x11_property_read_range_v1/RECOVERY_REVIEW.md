# Recovery review: Issue #3997 property read-range boundary

The old 2026-09-22 branch contains only `FREEZE.json`. It binds eight source,
environment, and plan identities, but the bound source archive, formal rows,
worker outputs, execution receipt, audit JSON, and mutation results were not on
the branch or in current `main`. A bounded search of accessible local
workspace/temp paths found no matching package.

## Issue-reported formal result

Issue [#3997](https://github.com/Unjuno/agent-interface/issues/3997),
comment [5766748866](https://github.com/Unjuno/agent-interface/issues/3997#issuecomment-5766748866),
reports one 24-case run, three workers and private Xvfb servers exit/reaped,
an independent raw-only audit with no errors, and 12 rejected mutations. It
reports `PASS_PROPERTY_READ_RANGE_BOUNDARY_SCOPED`: the predecessor comparator
returned false whole-endpoint equality on six partial-read pairs; the
range-aware wrapper returned UNKNOWN 12 times, SAME 9 times, and DIFFERENT 3
times, while refusing prefix-truncated and wrong-type replies.

The Issue reports hashes for RUN.json, three format-specific worker/raw
outputs, AUDIT.json, MUTATIONS.json, and EXECUTION.json. None of those files
was recovered here, so the hashes, counts, and audit outcome remain
Issue-reported and are not independently checked from bytes in this
repository. The reported wrong-type `bytes_after` 12/6/3 discrepancy and its
bounded interpretation are retained; no normalization or general X11
conformance claim is added.

## Recovery boundary

`FREEZE.json` is preserved byte-for-byte. No X11 server, worker, or formal
case was rerun. The original full-read predecessor result and its publication
limits remain separate. This record does not promote a runtime change, infer
temporal history, or claim arbitrary-application/task/model benefit. Any
later-recovered evidence should be audited from its original bytes without
rewriting the historical allocation.
