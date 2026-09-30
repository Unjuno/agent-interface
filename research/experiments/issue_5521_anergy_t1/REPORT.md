# T1 host construction result — Issue #5521

## Outcome

PASS_SCOPED for the finite host-only simulator. The exact JSONL output is in
raw-host.jsonl; run.py emits the frozen schedule and all three policy traces.
audit.py independently replays the persisted records and returns
PASS_SCOPED. test_t1.py also changes the same-generation contradictory row to
ADMITTED/effect=true and confirms that the independent auditor rejects it.

| Policy | Verifier checks | Admitted effects |
|---|---:|---:|
| Stateless | 8 | 5 |
| Permanent rejection | 4 | 2 |
| Reversible anergy | 5 | 3 |

The anergy state survives two JSON serialize/reload restart boundaries within
the simulator; this is not an OS process crash/relaunch test. It
refuses a same-generation SAFE contradiction after UNSAFE evidence, refuses
same-generation evidence after restart, reactivates proposal P only with SAFE
evidence at authority generation 2, and expires proposal Q at its frozen tick
without allowing the old fingerprint to act. Q with a different target and
new proposal R remain separate candidates.

## Build/experiment failures retained

The first simulator fixture set expiry on P too early, so the pre-expiry fresh
generation reactivation assertion failed. While tightening the fixture, a
repeated already-admitted proposal also counted as a second admitted effect;
that exposed a schedule/model ambiguity, so the duplicate-admission row was
removed from this policy-comparison schedule rather than silently counting it
as safe. The final frozen schedule retains an unsafe duplicate to measure
verifier amortization and separately tests fresh-generation recovery and
expiry. These are harness/construction corrections, not scientific FAILs.

## Scope and disposition

This run used the host Python 3.12 standard library; no Docker/OrbStack command,
model, network, GPU, GUI, or live input was used. The shared #5085 CPU lane has
no explicit assignment for #5521. This is construction evidence only, pending
one authorized network-disabled Linux-container reproduction and audit.
The finite, hand-authored event schedule does not establish semantic proposal
identity, GUI safety, safe-probe non-interference, crash consistency under
storage faults, threshold robustness, fairness, or production usefulness.
Do not promote this to an integrated runtime PASS.

## Parallel T1 comparison

After this run, Issue #5521 received another agent's T1/T2 comments
(#5913135096 and #5913149677). Those traces use an explicit expiry that permits
a fresh same-generation check after expiry. This run deliberately keeps an
EXPIRED tombstone for the old proposal fingerprint and requires a new
fingerprint to re-enter. The differing outcomes are a policy choice, not
replication agreement: neither schedule establishes which expiry semantics are
preferable. Preserve both results; compare them in a preregistered container
extension rather than overwriting either record.

## Reproduction

From repository root:

```sh
python3 research/experiments/issue_5521_anergy_t1/run.py > raw-host.jsonl
python3 research/experiments/issue_5521_anergy_t1/audit.py < raw-host.jsonl
python3 -m unittest discover -s research/experiments/issue_5521_anergy_t1 -p 'test_*.py' -v
```
