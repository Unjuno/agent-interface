# Result — OpenTTD input/effect transfer eligibility

## Outcome

**HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN.** The frozen trace preserves useful
evidence of an input request and a later verified-neutral terminal, and the
independent game observer records a partial A-to-B task effect. The records do
not identify actual per-button occupancy or join that effect to the host
monotonic input timeline. The independent audit confirms the HOLD, not a latency
or occupancy estimate.

## Executed work

- Owner/task: Windows local Codex task 01a0b990-3d17-72f1-a908-9a2072104ce5.
- Work ID: OPENTTD-R133-EFFECT-JOIN-20261001-01.
- Frozen input base: main b63fe0812e5816163105bdf37384c5f1dd407760.
- Local host: Windows, CPython 3.11.9; candidate 14:50:32–14:50:58 UTC.
- Main advanced to 871c0aca73fae16552977975f584c7d3c6ed56a8 during the frozen
  run window. Its four-commit diff from b63fe08 touches other research/index
  paths; CURRENT_GOAL, ROADMAP, and all three pinned inputs are unchanged. The
  result remains explicitly bound to b63fe08, not relabeled as a run against
  the later tip.
- Construction v2: 5/5 corruption tests passed. Revision 1's 4/5 failure is
  preserved in README; no candidate or auditor ran under revision 1.
- Candidate: exactly one invocation, exit 0.
- Independent CPU raw-only auditor: exactly one invocation after candidate
  exit 0, exit 0. It does not import the candidate.
- Retries: 0. Candidate and auditor ran offline over local copies fetched
  read-only from the frozen GitHub commit. No model, GPU/CUDA, fit, game, GUI,
  OS input, Docker, WSL, or prior allocation was used.

## Reconstructed observations

- Runtime ledger: 311 rows; 29 pointer admissions; 7 button-down admissions;
  zero button-up admissions, across 6 program IDs.
- Each of the 7 down records joins by program ID to a terminal verified with
  empty buttons and keys.
- The measured input-ack-to-neutral-confirmation intervals range from
  319,502,382 ns to 1,411,871,874 ns. These are request/confirmation intervals,
  **not** held-button durations or release timestamps.
- Independent AIT observer: 263 records, two declared states; first A-to-B
  road state occurs at zero-based record 91. B-to-C remains absent and the
  full task score is false.
- Host runtime observations have capture_ns and sequence 1–52. AIT records
  have no shared sequence, event ID, or host-monotonic timestamp; their
  top-level fields are stage, x, y, width, tiles, edges, and guard.

Therefore an event index cannot be converted into an effect latency, and
program terminal neutrality cannot be substituted for per-button release.
Existing model-wait/useful-feedback aggregate totals do not repair this
missing lineage.

## Decision and scope

This is a one-episode retained-data eligibility result for Issue #59's r133
cross-domain transfer step. It is not a live test, a general OpenTTD conclusion,
a guard/effectiveness result, or evidence of human-tempo, safety, or MAP01
success. Keep occupancy and effect latency UNKNOWN until a future source
provides per-key release evidence and an independently timestamped effect
receipt with a validated clock/identity join.

## Provenance

Frozen input SHA-256 values and candidate/auditor code Git blob IDs are in
README.md. Candidate output is result.json; independent raw audit is
independent-audit.json.

The first GitHub output-publication attempt put a PowerShell path-expansion
error message in both JSON destinations (commits eed21a6 and af5dea2). The
local outputs were intact; the two branch paths were corrected from those
exact local files (commits b5b3b52 and a8da3f8). The scientific candidate and
auditor were not rerun. The correction is retained in branch history.

