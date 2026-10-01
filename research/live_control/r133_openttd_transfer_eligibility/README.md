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

## Execution plan

1. Verify the three input hashes and run the five construction/corruption tests.
2. Freeze the published candidate/auditor source hashes before the one candidate
   invocation.
3. Run the candidate once on the retained bytes.
4. If it exits 0, run the independent raw-only auditor once.
5. Preserve every status; no retries, substitutions, historical relabeling, or
   model/game/GUI/OS-input calls.

