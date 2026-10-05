# A04 STOP — current source changed before candidate start

A04 was frozen against main `ff677c7fc04ba72923ee375527ae39489728a0bd` and PR #7974 head `2a79899f41bf71ab41df8dd5dcf1cd9e70f9eca8`. The mandatory final remote-ref check, before any candidate invocation, observed main `2f2c83c3da36566bac410b13b2ed5202c9641f1a` and PR head `b5fbfed1c896f587dd5dfeb30c2735d63f670264` instead.

Disposition: `STOP_SOURCE_CHANGED_BEFORE_CANDIDATE`. Candidate invocations: 0. Auditor invocations: 0. No X server was started for A04. Preserve its freeze and source package unchanged. The changes were in V12 release error sampling and its tests; A05 is a separately frozen successor on the newly observed refs, not an A04 retry.
