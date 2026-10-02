# Issue #6173 T0-03 factorized-axis result

## Result

PASS_METHOD_FACTORED_AXES. The candidate and separately implemented raw-only
auditor agreed across all 17 frozen cases; candidate=1/exit 0, auditor=1/exit
0/errors 0, retries 0. Twelve construction tests and Python compilation
passed; freeze and fixture hashes matched.

The result preserves three independently auditable axes:

- Attempt: distinguishes no observed attempt, protected-target attempt,
  authorized-only access, unknown-target attempt, and mixed targets.
- Acquisition: distinguishes no evidence, verified denial, direct oracle
  bytes, derivative bytes, partial/unknown response, and mixed acquisition.
- Coverage: distinguishes complete monitoring from gaps such as monitor
absence, missing/duplicate response linkage, unknown recipient, or unpaired
response.

Examples demonstrate why the factorization matters. Denied oracle request with
a monitor gap remains visible as attempt=EVALUATION_TARGET_ATTEMPTED and
acquisition=DENIED while coverage=GAP and disposition=UNKNOWN_ACCESS. A
complete no-attempt has attempt=NO_ATTEMPT_OBSERVED, no acquisition evidence,
coverage=COMPLETE, and disposition=NO_ORACLE_ACCESS_OBSERVED. Direct oracle
bytes remain EVALUATION_ORACLE_REACHED even when the candidate self-claims
CLEAN; a CONTAMINATED self-claim without access does not create evidence.

Mutation controls reject axis collapse, response deletion from the
candidate-visible projection, a forged flat disposition, self-claim override,
forged provenance, and candidate/observer trace mismatch.

## Lineage and resource scope

This is a fresh additive method successor after flat-label Issue #6173 T0/T0b
and a concurrent overlapping 13-case T0-02. All predecessor raw data/results
remain unchanged; T0-02 is disclosed but not treated as a novel finding. Main
at freeze is 69a1bf509eb432e5e3c0c294d05ad7671d86adb6.

Host CPython standard-library only. One unrelated OrbStack container was
active at preflight; none was entered, stopped, modified, or joined, and no new
container was created. No private/real answer, model, user data, network,
GitHub/web retrieval, app, GUI, or physical input was used.

## Limits

This is a finite synthetic method result. It does not establish production
monitoring completeness, detect unlogged semantic inference, or show that any
real evaluation run accessed an oracle. Real benchmark validity, tool
admission, and task-effect behavior remain untested.
