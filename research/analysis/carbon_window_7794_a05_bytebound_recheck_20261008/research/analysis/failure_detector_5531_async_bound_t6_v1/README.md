# #5531 T6-E1 — asynchronous delay indistinguishability

## H / T / D / C / U

**H.** With no known upper bound on healthy response delay, a healthy-but-slow
subject and a crashed subject can have identical observer-visible histories up
to any selected finite timeout. A timeout-only detector must therefore make the
same deadline decision in both worlds. Typed suspicion can preserve that
distinction as unresolved and block routing without claiming terminal failure;
only a fresh authenticated heartbeat or an independent crash witness may later
separate the worlds.

**T.** On one frozen logical clock, enumerate deadlines 1, 3, and 5 ticks. For
each deadline, compare healthy-slow, crashed, and unauthenticated/invalid-response
worlds under timeout-as-failure and typed suspicion. Every world has no heartbeat
through its deadline. At the next tick, inject a fresh generation-1 heartbeat,
an independent crash witness, or an invalid unauthenticated response as
appropriate; after the crash witness, also inject a late generation-1 response.
The candidate emits JSONL transitions; a separate raw-only auditor replays them.

**D.** `PASS_ASYNC_DELAY_BOUNDARY_SCOPED_AUDIT_V2` requires byte-equivalent
observation prefixes within each deadline/policy group, identical decision
states across worlds at the deadline, suspicion blocking route without
revoking authority, healthy recovery only on an independently checked fresh
authenticated heartbeat, terminal failure only on the authenticated
independent crash witness in the typed arm, no stale response reactivation,
and no invalid-response clearing. The corrective independent audit rejects
eight evidence/state mutations, including the four originally preregistered.
The result is a finite counterexample to distinction from identical prefixes,
not a general timing theorem.

**C.** Observer authentication, witness independence, generation labels and
logical ticks are stipulated. The timeout-as-failure and typed policies share
the exact same pre-deadline observations. There are no effectful actions in the
simulation.

**U.** No real delay distribution, clock skew, correlated or malicious
observers, GUI effects, runtime integration, or production safety is tested.
This experiment does not resolve #5531 or prove failure-detector guarantees in
an asynchronous deployment.

## Frozen protocol and execution boundary

Base: main `b92f2abb21e796150287135a74599fea64cc9759`. Source and gates are
bound by `freeze.json` and `SOURCE_MANIFEST.json`. Construction tests are run
before the one candidate and one separate raw-only auditor process. The local
OrbStack Docker info probe timed out after 4 seconds; the `default` context's
`/var/run/docker.sock` is absent, and several pre-existing Docker clients were
blocked. No container was launched and no shared CPU/Docker allocation was
requested or consumed. This is a host-only exact finite enumeration, not a
container result.

## Executed result and correction history

The initial manifest-gated command at `results/t6-e1-01/` stopped before any
candidate process because the manifest contained one mistyped SHA-256. The
STOP is retained; candidate/auditor invocations were 0/0. A corrected freeze
then ran candidate once and v1 auditor once in distinct processes at
`results/t6-e1-02/`: candidate PID 32590, auditor PID 32591, 18 trials and 114
raw rows, raw SHA-256
`876868a980214b6659fc928969e3fb2e60449879105fd697c4c3c2c16a8ac0f6`.

The v1 auditor returned PASS, but a post-run challenge found it did not check
whether fresh-heartbeat and crash-witness rows actually declared authenticated
evidence, generation, and the expected observer domain. The v1 output and raw
remain unchanged, but that PASS is **not accepted for the full D gate**. One
corrective auditor-only invocation read the exact same raw bytes and passed
`PASS_ASYNC_DELAY_BOUNDARY_SCOPED_AUDIT_V2` at
`results/t6-e1-03-audit-correction/` (auditor PID 35787; candidate invocations
0). Its nine construction controls passed: missing heartbeat authentication,
wrong generation, unauthenticated crash proof, wrong crash domain, routing
during suspicion, stale-response reactivation, invalid-response clearing, and
missing event all rejected.

| Gate observation | Result |
|---|---:|
| Matched prefixes, worlds identical through deadline | 6/6 groups |
| Healthy-slow permanently failed at timeout by baseline | 3/3 deadlines |
| Healthy-slow permanently failed by typed suspicion | 0/3 deadlines |
| Crashed world reaches FAILED after independent witness | 3/3 deadlines |
| Stale reactivation / invalid-response clearing / effectful actions | 0 / 0 / 0 |

This tests a finite logical-time model with stipulated authentication and
failure-domain labels. It neither measures deployment behavior nor closes
Issue #5531, which remains open for real timing and observer assumptions.

## Reproduction

From this directory:

```sh
python3 -B -m unittest -v test_audit test_audit_v2
python3 -B run_experiment.py --results results/t6-e1-reproduction
tmpdir=$(mktemp -d)
python3 -B audit_v2.py --raw results/t6-e1-02/raw.jsonl --freeze AUDIT_V2_FREEZE.json --output "$tmpdir/audit-v2.json"
```

The recorded result directories are immutable and intentionally refuse
overwrite. The first command creates a new reproduction directory; the direct
audit-v2 command writes outside the retained results tree. The execution receipt
for the recorded audit correction is already retained by `run_audit_v2.py` and
must not be regenerated in place.
