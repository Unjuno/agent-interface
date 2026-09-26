# Issue #4516 MAP01 15-second refresh result handoff

## Provenance and scope

This additive handoff records the one-time formal allocation reported in the
Issue [#4516](https://github.com/Unjuno/agent-interface/issues/4516) comment
dated 2026-09-26 15:35 UTC. It does not replace the formal raw bundle or claim
an independent re-audit of bytes that are not present in this checkout. The
comment identifies the raw artifacts, byte counts, SHA-256 digests, and
`V10_RESULT_AUDIT.json` path; those files still need to be published and
read-back verified before a reviewer can independently reproduce the audit.

The prior #4513 allocation (seed 990636) remains an immutable
`STOP_CONTAINER_SOURCE_MOUNT_INCOMPLETE`; it is not reused here. The successor
formal allocation below was run once, and its seed and result path are consumed.

## H / T / D / C / U

- **H:** A 15-second observe-only inter-segment lease permits the no-visible-
  effect refresh to complete while retaining the existing clock, freshness,
  ownership, typed-input, and release guards.
- **T:** Issue #4516; seed `990637`; pinned OrbStack image
  `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`
  (`linux/arm64`); WAD SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`;
  24-decision maximum, `gpt-5.6-luna`/low, session span 4.
- **D:** The Issue result reports all 3 inter-segment observe-only refreshes
  accepted and completed, with translated lease horizons 14.996490500s,
  14.996784167s, and 14.997298667s; 9 model-authored primary action programs
  completed. Thus the specific 5s-to-15s refresh hypothesis is supported for
  this episode. The allocation as a whole is
  `HOLD_INCOMPLETE_24_DECISION_CLOCK_BOUNDARY_ERROR`: it stopped at decision 8
  with a final-action admission clock-boundary `ValueError`, after 8 model
  turns. No `report.json` or final score exists, so this is neither a 24-turn
  gameplay FAIL nor a MAP01-clear result.
- **C:** Per the Issue result, 409 exact and typed observations were retained;
  40 physical input admissions occurred; all 27/27 owner releases were
  independently reported as verified empty. The frozen effective controller,
  20 runtime-source hashes, and WAD hash were reported matching their freeze.
  No retry is authorized. The raw planner protocol, runtime events, owner
  releases, deadline translations, STOP report, and machine-readable audit
  must remain additive at the paths recorded in the Issue comment.
- **U:** The exact causal boundary/clock mismatch is unisolated. One episode
  does not establish a general refresh policy, gameplay reliability, or map
  completion.

## Local container regressions run in this task

Using the pinned image on OrbStack with `--platform linux/arm64`,
`--network none`, and a read-only root:

- The repository's v39 controller regression passed 2/2 tests. This is
  controller regression evidence, not a test of the formal adapter's entire
  app-server/model path.
- A five-case synthetic lease-contract harness passed 5/5: 15-second horizon
  remains above the strict 5-second post-probe margin; expired and over-30s
  horizons reject; just-under-margin holds; and observe-only completion
  requires a completed terminal plus verified empty keys/buttons. This harness
  is a boundary model, not the Executor implementation and not formal MAP01
  evidence.

The Issue comment separately reports its complete-source preflight and
executor controls. Those reports are intentionally distinguished from the
two local checks above.

## Raw evidence readback status

**HOLD — raw bundle unavailable in this checkout at handoff time.** The Issue
comment reports these SHA-256 values, which are transcribed here but have not
been recomputed from the corresponding files in this repository:

| Artifact | Reported SHA-256 |
|---|---|
| `planner-protocol.jsonl` (508,450 bytes) | `90049bffeedd8b484bd1fa6172cf36bd874d788e59b7261682a18af2242c331d` |
| `runtime/events.jsonl` | `4360a998ac6b62d41075dab7b7673d0e9f5373d14bb1693ed4f71d993f1b1d2d` |
| `runtime/owner-events.json` | `033bb67d8956e9699bd5f202ade9095b2bc6b776a299cc56e2b64135b945699e` |
| `runtime/lease-deadline-translations.jsonl` | `4b92928c41bfbb09925640f68a7529ac20ee329b446fd43724ad8234c7e0de33` |

The reported immutable result directory is
`research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-02/`.
Do not mark this handoff independently audited or treat the missing raw bundle
as an experiment PASS. A follow-up integration commit should include the
original files, freeze, STOP report, and auditor, then rerun read-only hash
and semantic checks without rerunning the consumed allocation.
