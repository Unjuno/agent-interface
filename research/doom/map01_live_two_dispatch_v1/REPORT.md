# Real MAP01 live two-dispatch authority/freshness transfer v1

Status: **PASS_MAP01_LIVE_TWO_DISPATCH** for a frozen zero-model ViZDoom/X11 authority/freshness block. No task-success/gameplay-efficacy/model claim.

## Question

Does the live two-dispatch capability rule survive transfer from the rendered X11 tracker to the real retained MAP01/v13 measurement stack?

The rule remains unchanged:

1. a first physical capability ends independently at its owner deadline;
2. release must be verified empty;
3. one bounded passive post-authority observation is evidence only;
4. a second input may be considered only from a strictly newer current observation;
5. the unchanged adaptive caller v3 still performs ordinary reuse/final revalidation;
6. the second physical input is a separate new submit/Lease;
7. reusing the post-authority observation as current must stop before any second input.

## Runtime path

- retained real ViZDoom/X11 MAP01 stack from runtime base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- `map01-threat-contact-v2` fixture, skill 1;
- exact dual-lifetime Executor source SHA-256 `0b06daf675c7ff83e618f6220847b3fc1796d7281e2e236ea4f57b66f17f3d07`;
- exact quiet-hold backend SHA-256 `71c86a6c953f3a60b6a2c0c5d8c71435c2164e0fb1dbe74759d17cbf49487bcf`;
- exact adaptive caller v3 Git blob `7faf042304728ce91a3e4f89d465b251ea0bf70d`;
- zero model calls.

A local session adapter differs from the retained wrapper only in filesystem path wiring (`/mnt/data/runtime-preview-extracted` instead of the earlier `/tmp/lab/src`). The Executor/backend scientific sources are byte-identical to the retained discovery sources.

## Conditions

First program in every arm:

- source observation sequence 1;
- `Shift_L` hold requested for 2000 ms;
- owner authority deadline 600 ms;
- terminal must be `authority_ended`;
- owner expiry release verified;
- one passive post-authority observation, sequence 2, within its independent lifecycle deadline.

Then:

- **FRESH**: submit one observe-only program from sequence 2, obtain sequence 3; pass ordinary caller `reuse_revalidate -> final_revalidate`; submit a separate Right hold (120 ms) under a new Lease. `verify_effect` deliberately returns `unavailable`, so the caller must end as `TASK_NOT_VERIFIED`, not task success.
- **STALE**: use sequence 2 as the current observation without a new observe-only program. Caller must `SAFE_STOP / stale`; no Right input admission may occur.

Three matched pairs use fresh seeds `994101..994103`, with alternating order F/S, S/F, F/S.

## Construction failures retained

- **smoke-01**: the harness treated one 0.5 s event-queue gap as the entire terminal timeout. No formal sample was consumed. The wait loop was repaired to continue until the overall deadline.
- **smoke-02**: core behavior passed, but the audit joined `input_admission` by program id even though these events carry key/intent-token rather than program id. It therefore reported FRESH second input as 0 and STALE as 1. No formal sample was consumed. The audit was repaired to count the physical `Right` admission directly and to retain owner-expiry/terminal-score evidence.
- **smoke-03**: passed the repaired construction boundary and was not pooled into the formal block.

## First frozen formal outcome

Decision: **PASS_MAP01_LIVE_TWO_DISPATCH**.

Across all three matched pairs:

- FRESH: **3/3** hard-gate PASS;
- STALE: **3/3** hard-gate PASS;
- FRESH Right input admissions: **3**;
- STALE Right input admissions: **0**;
- every first terminal: `authority_ended`;
- every post-authority receipt: `captures=1`, sequence advanced, inside lifecycle deadline, no error, no authority regrant, no old-tail resumption;
- every arm: exactly one owner `expired` release, expiry release verified, all owner release records verified;
- terminal independent-scorer agreement audit: **6/6 PASS**;
- FRESH second program: **3/3 completed**, release verified;
- FRESH caller: **3/3 `TASK_NOT_VERIFIED / unavailable`**, exact call order `reuse_revalidate, final_revalidate, execute, verify_effect`;
- STALE caller: **3/3 `SAFE_STOP / stale`**, calls only `reuse_revalidate`.

All six terminal independent scores were `0 kills / 0 deaths / no MAP01 exit`. That is deliberate negative scope evidence: this experiment validates authority/freshness handoff, not useful-control efficacy.

Formal first-result SHA-256: `9e2b917992d6c96c9d5ab7417cf0e52a1ecd3ff073f08cca0d981ceda5c5f895`.

## Interpretation

The capability boundary now survives a real ViZDoom session:

- the expired first action cannot authorize the second;
- the post-release observation is necessary but insufficient;
- a newer observation is required before new physical input;
- the second action obtains a fresh Lease;
- stale current evidence results in zero second input;
- physical admission correctness is kept separate from task-effect verification.

The final point matters. FRESH deliberately does **not** return `TASK_SUCCEEDED`: a correctly admitted Right turn is not evidence that a strategic MAP01 objective was achieved.

## H / T / D / C / U

**H.** The sequence-bound post-authority replan rule can transfer to real MAP01 without stale capability carryover.

**T.** Three alternating matched pairs / six real ViZDoom-X11 sessions, exact retained dual-lifetime/quiet-hold mechanisms, exact caller v3, independent scorer agreement audit, zero model calls.

**D.** PASS at authority/freshness scope because all fresh arms admit exactly one second Right input through a new Lease after sequence advance, all stale controls admit zero, and all release/scorer gates pass.

**C.** Fresh sequence alone does not imply useful strategy or target semantics; a later live planner could still choose a bad action. This block intentionally returns TASK_NOT_VERIFIED after physical execution.

**U.** One fixture, one short second action, no model, no kill/progress outcome, no external concurrent mutation, one host family. The next gate should attach a task-relative observable validity/effect predicate to the second dispatch or run one separately frozen model-in-loop handoff; do not convert this admission result into gameplay success.
