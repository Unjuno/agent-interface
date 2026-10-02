# OpenTTD input/effect transfer eligibility audit

Status: prospective, read-only retained-evidence audit for the r133 next step in
Issue #59. It is not a live game/model experiment or a shared-runtime allocation.
No prior raw artifact is changed.

Host-only work identifier: OPENTTD-R133-EFFECT-JOIN-20261001-01, owned by the
current Windows Codex task 01a0b990-3d17-72f1-a908-9a2072104ce5. This is a
bounded local-CPU retrospective parse, not an exclusive GPU/Docker/WSL lease
and not a reservation of a shared runtime.

## H / T / D / C / U

- **H:** The retained OpenTTD v6 episode contains identity-bound input
  admission/neutral-release evidence and an independently scored task-state
  transition, but the source records may not support either exact held-button
  occupancy or a causal host-time join from actuation to useful task effect.
- **T:** Parse only the three SHA-pinned retained files below: runtime
  events.jsonl, the independent AIT observer records in game-stderr.txt, and
  posthoc-audit.json. Reconstruct event counts, button-down-to-terminal neutral
  receipts, the first A-to-B observer transition, and shared clock/ID fields.
  No model, game, GUI, OS input, network service, Docker, WSL, or GPU.
- **D:** Report HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN if actual per-button-up
  time is absent and the independent effect stream has no clock/sequence/ID
  shared with host observations. Do not label request-to-neutral time as
  button occupancy or call an observer record index a latency endpoint.
  Any source/count/identity/release/observer mismatch is a FAIL of this audit.
- **C:** A matching terminal record verifies that the owner later observed a
  neutral state, but it does not timestamp the individual button-up. Pixel or
  frame-sequence evidence and the independently scored AIT state can coexist
  without a causal clock mapping.
- **U:** One archived OpenTTD episode only. No live held-input duration,
  first-useful-effect latency, guard effectiveness, human-tempo, general
  cross-domain transfer, or task-success claim.

## Frozen source set

Repository Unjuno/agent-interface, exact main commit
b63fe0812e5816163105bdf37384c5f1dd407760. The three raw input Git blobs are
identical at this base to the previously inspected f0139613 commit.

| Role | Path | Git blob | SHA-256 |
| --- | --- | --- | --- |
| Host/runtime events | research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/events.jsonl | 8ccb166927329313bb316b2cd40208c49119c10c | b9e707b006a918b232f6d8915adc6a95e4d7e4ee789fec7ef4e1fba7e2df61ae |
| Independent game observer | research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/game-stderr.txt | 1a5c1167d15cddf674ad9060f3d44bbedcfcf005 | 4bcfb5b2632e9b2dc76f5e3f67a73f30cbd6b142578b495f0b204a2ec9696ca4 |
| Existing posthoc summary | research/live_control/results/timing-envelope-openttd-l-06/posthoc-audit.json | 4875434559d95b7049bc4e4aa278e496e46a2f6e | 8377e663d6f3b88eb41b73d85212f903f21b4879010835f9e2d1f100de4bee5c |

The audit reads local copies of these exact immutable files. The candidate and
independent auditor are separate programs; the latter must not import the
candidate. Five corruption tests cover row loss, fabricated button-up, broken
identity, unverified release, and non-neutral release.

## Frozen analysis sources — before execution

Construction revision 1 was frozen at commit
551dd86ef7e3455b1c310b62a41a9ac50226735a. It failed corruption test 02 and
was not used for the candidate. Revision 2 is frozen at branch commit
a22e5f7e11cda77f99194939c201560cd83b00a9. Exact current Git blobs:

| Role | Path | Git blob |
| --- | --- | --- |
| Candidate | research/live_control/r133_openttd_transfer_eligibility/audit.py | 7dee30e396acbcb088cf8ec58cd97f9220f64239 |
| Independent auditor | research/live_control/r133_openttd_transfer_eligibility/independent_audit.py | f88d0345bb4e3f24ad0fc18e7826b00ce09f9214 |
| Five corruption controls | research/live_control/r133_openttd_transfer_eligibility/test_audit.py | f93885a90a98dc0b8b93faf959fede7775500b8c |

The local Windows working copies were byte-for-byte text-compared with these
three branch files. These revision-2 code blobs are immutable for the candidate
and raw-only audit; any correction would be a new successor and would not
replace this result.

Construction revision 1's first host test run failed only the fabricated
button-up corruption control (4/5 passed). No candidate or raw-only auditor was
invoked. The failure is preserved here; revision 2 adds an explicit frozen
7-down/0-up coverage invariant to candidate and independent auditor. This is a
pre-execution construction correction, not evidence about the hypothesis.

## Execution plan

1. Verify the three input hashes and run the five construction/corruption tests.
2. Freeze the published candidate/auditor source hashes before the one candidate
   invocation.
3. Run the candidate once on the retained bytes.
4. If it exits 0, run the independent raw-only auditor once.
5. Preserve every status; no retries, substitutions, historical relabeling, or
   model/game/GUI/OS-input calls.

## Executed result

Revision 2 construction passed 5/5 corruption tests. The one frozen candidate
ran once and exited 0; the separate raw-only auditor ran once and exited 0 with
PASS_RAW_AUDIT_OF_HOLD_CLASSIFICATION. The research disposition is
HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN, not an occupancy or latency estimate.

At candidate start main had advanced from frozen base b63fe08 to
871c0aca73fae16552977975f584c7d3c6ed56a8. The four-commit comparison showed
no change to CURRENT_GOAL, ROADMAP, or any pinned source blob. The result stays
bound to the exact b63fe08 base and is not represented as run against the later
main tip.

Candidate output SHA-256:
3b3126c30dfaa1e6e1c7e8a6b0dd82aa2872787e45108a829388f16ca4987349

Independent audit output SHA-256:
f7053023be0422c0837ccea827ddef691d000a35b0c847ba7520c2697edab773

Full run accounting is in RUN.md; interpretation and scope are in RESULT.md.
The JSON outputs are result.json and independent-audit.json.

Publication note: the first output upload accidentally stored a path-expansion
error in both result paths (commits eed21a6 and af5dea2). The exact local JSON
outputs were uploaded correctly afterward (commits b5b3b52 and a8da3f8); the
candidate/auditor were not rerun, and the correction remains visible in branch
history.

