# Independent preparation review

Reviewer Curie `01a1036a-b28d-7491-8615-e3f6842803e5` (read-only, now closed).
Base `12e4c1ebaf382d70760eafbe3cf2e5fda90a9d2c`.
Reviewed head `3c4fb067696da9082166fe6f24e56154066c3f13`.
Independent HOST result: 8/8 construction tests pass.
Critical: none identified within preparation scope. NOT merge/live-ready.

## Important findings

1. Controller imports map01_stagnation_v1 before inserted dependency-root setup.
   Generated standalone launch can fail before setup or select an unrelated
   same-named module. Existing command-function extraction misses this.
2. Source custody hashes predetermined sibling paths, not actual resolved
   imported modules. Bare imports can select an earlier-path module while the
   receipt hashes a different file. Four original pins also do not freeze all
   inherited dependencies. Bind resolved imported paths/hashes before claiming
   composed provenance. This is a gap, not observed substitution.

## Minor findings

3. Missing preservation controls: foreign-lease up, invalid focus, expiry/cancel,
   press/up telemetry clocks and record append failures. Inspection finds guards
   unchanged, but current tests do not protect all stated requirements.
4. Historical six-test CONSTRUCTION_CI.json lacks exact tested builder/test
   hashes or tested tree identity. Keep it historical; do not retrofit current
   hashes as contemporaneous proof.

## Scope / disposition

Inspected original guard branches, request/sync ordering, explicit-up None
return and ordinary Exception handling are preserved. Original release-record
failures, BaseException and hard-deadline guarantees are outside this repair.
Independent useful TASK_EFFECT, full controller/native/game and scientific
completion are unexecuted. Suitable to proceed with non-live import preparation
only, with Important findings as unresolved gates.

## Subsequent parent correction (not covered by original reviewer verdict)

Finding 1 reproduced in generated-prefix boundary test: nine tests, one FAIL,
exit 1. Moved setup before first local import in derived controller only.
Nine HOST tests then passed. Prefix executes actual generated setup/import
with a controlled import boundary; it is NOT complete real import execution.
Finding 2, both minor findings and full-route qualification remain open.
