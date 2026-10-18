# Current-main integration of early health monitoring

This addition qualifies integration; the original README/replay/result remain
byte-for-byte historical evidence from PR #8866 head
`eb1367cc3ac1184862c454440a418dcf1add9267`. Its dated ownership statements are
not current resource grants or new global prerequisites.

Base `fc4c5a5eba0616f13c071715aeed858b08855157` still evaluated health-only cover
from full artifacts. The candidate monitor is now composed with the current V39
caller. Typed health is validated and evaluated before the artifact extractor;
hard/unknown outcomes request a new decision and grant no input authority.
Matching typed/full projections coalesce only once per transport kind and epoch.
Increasing sequence numbers must also carry strictly advancing capture times.

Three new regression methods check both timestamp reversal/equality and both
transport orders, plus actual `build_cover_monitor` to
`drain_pending_observation_events` with hard health arriving before any artifact.
The source reader runs once for admission; no new artifact reader call occurs
for the typed decision. These are controller-boundary checks, not a complete
executor cancellation or independent task-effect demonstration.

First new run had five errors: four exposed accepted bad epochs, and one was
our incorrect fixture call signature. After repairing the fixture, four explicit
assertion failures reproduce the timestamp/repeated-pair gaps. Both original
logs remain under `health-typed-epoch-*-red*.log` in local consolidation outputs.
After the fix, the focused suite passes 13 tests. The broader original candidate
scope plus current-caller additions passes **138 tests normally and 138 under
optimized Python**, no skips. No real Codex/model/server/GUI/WSL/input was launched.

The saved report/events retain SHA-256
`719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` and
`2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
Normal-Python execution of the original replay against integrated source
`a0f1c2ec2bb1dfaa4e64f080bd6b53bf36a61b2f`, monitor Git blob
`eb18f001f2da5219abdba2540b1c28cc29de1573`, reproduces three soft and one hard
outcome with zero pre-decision artifact reads. The new
`integration-currentmain-replay-20261016.json` is separate from `result.json`.
The original replay uses Python assertions: it is not used as an optimized-mode
auditor or claimed as an independent validator. Unit-test assertions remain active
in the optimized integration suite.

This adopts the health-only event-handling repair and reduces one known
artifact dependency. It does not establish post-fix live delivery/latency,
physical release bounds, repeated recovery, MAP01 exit, matched efficiency or
independently verified task success. The retained 150 ms injected-delay study in
PR #8871 is a separate comparison, not new live evidence for this source.
Issue #59 and the overarching goal remain open.

## Review repair: typed numeric domains

Review found that the candidate checked integer type without applying the shared
DOOM domains. Synthetic health 201 and invalid ammo could preserve the policy.
The new domain regression first reproduced three failures; its raw is retained
as `health-typed-domain-red-first.log`. The fix calls the existing shared
`signal_value_in_domain` for both typed projections. Out-of-domain values become
UNKNOWN, require a new decision and do not invoke artifact readers. Health zero
is outside this typed observed-value domain; the controller's separate terminal
health handling remains unchanged.

Final executable source `d478afc3e3d343111d1be58870d18a011bacf37f` passes
**139 tests normally and 139 optimized**, no skips, including four new epoch/domain/
caller test methods. The four retained sample outcomes also reproduce on this
source in `integration-domain-repair-replay-20261016.json`; the earlier integration
replay is retained separately. No formal experiment was rerun and no post-fix
live performance is inferred.

The first domain-repair replay invocation omitted the original README's
`PYTHONPATH=research/doom;research/live_control` prerequisite and failed to import
the shared domain module. That invocation produced no result JSON; its empty
stdout log remains separate and the tool transcript retains the import error.
The successful new output uses the documented path prerequisite, with additive
`health-typed-domain-repair-with-path-replay.*` local files. The source was not
changed to relabel this environment failure. Package tests and the direct DOOM
entry use the same shared validator through their existing import paths.
