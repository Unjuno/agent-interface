# MAP01 physical-occupancy admission audit supplement v2

The frozen R1 evaluator can accept physical DOWN/UP pairs without establishing that
they belong to the program the executor actually accepted. This supplement checks
that missing connection in a separate, read-only audit. The original R1 sources,
experiment identity and results remain intact.

**Retained decision: `PASS_OFFLINE_ADMISSION_CONTROLS`.** Twenty-three deliberately
inconsistent synthetic traces pass the frozen evaluator and are rejected by the
supplement. A consistent synthetic trace and the real Executor v12 lifecycle with
a synthetic backend pass both. An unconfirmed physical edge remains rejected by
both. These controls establish audit behavior, not successful physical actuation.

## Why this matters for interface refinement

The interface needs to distinguish accepted intent, physical input, observed
state and useful task effect. Measuring time between unrelated records would make
a latency or coverage improvement appear stronger than the evidence supports.
This work strengthens the accepted-intent-to-input connection before using
occupancy as an optimization signal.

For example, changing only the accepted intent token to a foreign token leaves
the frozen evaluator's result at PASS. Its physical-pair comparison only relates
the DOWN/UP records to one another. The supplement also relates both records to
the accepted program and therefore refuses this trace.

## Evidence and scope

| Check | Frozen R1 evaluator | Supplement v2 |
|---|---|---|
| Consistent synthetic two-key trace | PASS | PASS |
| Actual Executor v12 lifecycle, synthetic backend | PASS | PASS |
| 23 synthetic integrity corruptions | Accepts 23/23 | Rejects 23/23 |
| Unconfirmed physical DOWN | Rejects | Rejects |
| Missing/malformed admission or terminal evidence | Incomplete coverage | Refuses |
| Full scientific R1 gate | Separate experiment | Never granted here |

The 23 controls cover missing/duplicate acceptance, incorrect accepted ID, token,
program hash or deadline, missing/wrong submitted program, a release batch
attached to the observe step, edges outside the accepted lifecycle, incorrect
step counts/timestamps, nonempty/unverified terminal release, and missing/wrong
reported source hashes. The cases were designed while inspecting the evaluators;
they are construction controls, not a held-out accuracy estimate.

The retained [JSON result](OFFLINE_AUDIT_RESULT.json) contains all case names and
refusal reasons, LF-normalized SHA-256 values for the three supplement scripts,
Git blob identities of the comparison dependencies, and the six expected R1
runtime source hashes. Its SHA-256 is
`b05fefd6256a66259d0498ff587cbbb918126f53724e6cd1cd44818c18dd2e89`.

The real-executor control uses the repository's Executor v12 for acceptance,
attestation, token creation, step completion and terminal publication. Its
backend emits synthetic edges and performs no OS input or 250 ms physical hold.
The small hand-built trace also contains synthetic timestamps/source hashes.

The supplement reuses the frozen R0 bridge for physical-pair validation and adds
separate checks for:

- exactly one submitted and accepted fixed `hold(['a', 'd'], 250 ms); observe`
  program and one completed terminal;
- the submitted program's exact attestation and accepted input token/deadline;
- two DOWN records, one two-key hold, two completed steps and the matching release
  batch bound to step 0;
- edge, hold acknowledgement, step completion and terminal release ordering;
- a verified empty terminal release;
- agreement between six pinned source hashes and runtime `sources.json`.

Reported hashes are provenance metadata. They do not independently attest what
process executed, and the six hashes are not the entire transitive import graph.
The separate gates remain: unique authorized launch, fixture/engine identity,
physical interval precision, external process cleanup, and useful task effect.
The supplement always emits `full_r1_gate_eligible: false` and
`grants_input_authority: false`, including when its own checks pass.

## Reproduce the offline checks

From the repository root, with Python 3.10+ and Git:

```sh
python -m unittest discover -s research/doom/map01_v12_physical_occupancy_audit_v2 -p test_audit.py -v
python research/doom/map01_v12_physical_occupancy_audit_v2/record_controls.py --check research/doom/map01_v12_physical_occupancy_audit_v2/OFFLINE_AUDIT_RESULT.json
```

Both commands pass on Windows and Ubuntu/WSL; the retained result matches on both.
There are seven unittest methods, including the 23 corruption controls, malformed
evidence controls, a real-executor schema check and a frozen-source lookup.

The first WSL frozen-source lookup failed because Git could not resolve the
Windows-created worktree's absolute `.git` path. Repeating the offline checks
with `GIT_DIR` and `GIT_WORK_TREE` mapped to their `/mnt/c/...` locations resolved
that harness issue. No runtime source or scientific allocation was changed.

To inspect a retained runtime directory:

```sh
python research/doom/map01_v12_physical_occupancy_audit_v2/audit.py --runtime /path/to/runtime --program-id r1-physical-occupancy-1
```

The directory must contain `events.jsonl` and `sources.json`. Run the frozen R1
audit and all other applicable gates separately. Source drift causes refusal;
a successor source identity requires its own explicitly reviewed expectations.

## Relationship to the failed live attempt

As observed on 2026-09-19,
[Issue #1928](https://github.com/Unjuno/agent-interface/issues/1928) retains an
import-cycle startup failure in
[workflow run 35441624906](https://github.com/Unjuno/agent-interface/actions/runs/35441624906).
Its recorded construction/formal attempts yielded zero completed formal sessions
and zero measured actuations. This supplement neither repairs that startup
failure nor converts it to a physical-occupancy result. No live game, model,
construction or formal session was launched by this supplement.

The next physical-occupancy successor should carry these admission and terminal
checks into its complete audit after repairing and freezing its import graph.
Only then can measured occupancy support a matched interface comparison. The
current result establishes no gameplay gain, model-latency reduction, token
saving, cross-domain transfer or human-tempo performance.
