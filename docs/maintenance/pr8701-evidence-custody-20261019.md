# PR #8701 MAP01 A03–A07 evidence custody review (2026-10-19)

PR [#8701](https://github.com/Unjuno/agent-interface/pull/8701), exact head `44f15471bd07705f1bbe565c017b6f9df29e87ec`, contains 41 research files for distinct MAP01 A03–A07 allocations plus one separate `docs/CURRENT_GOAL.md` addition. None of the 41 research paths is in main `5f72d52abbb97c0de05166ae5b0b9bb6419fd6ad`; the frozen source commit `4fb44827372c1fe4872a1add532c12544a5a9f81` is reachable from main. The A03–A07 packet does not overlap the A01/A02 artifacts from #8678.

## Result and audit distinctions

- A03–A06 are recorded as one-shot setup STOPs with unique IDs. They were not retried in place.
- A07 completed 10 planner turns in 41.60 seconds of control time, remained alive but unfinished, with zero kills, no deaths, and no MAP01 exit. Health ranged 100→82 and ammo 48→36. Neither the preregistered hard-health guard nor a useful independent scorer event occurred during pending inference; the overall preregistered result is HOLD.
- Audit v1 emitted FAIL. Additive v2 reconciled cancellations against admissions and recorded scoped release evidence. Audit v3 on the saved trace still returned FAIL because five of six admitted cancellations had one fewer explicit transition row than admission rows. A separate owner-release receipt-chain reconciliation matched all 10 cancellation IDs and is labeled `PASS_CUSTODY_RECONCILED_SCOPED`, with `formal_pass=false`. This is X11 server-side custody evidence, not proof of physical key state, game consumption, threat-control efficacy, or task success. The versioned audit corrections and tests must remain separate from the original raw/v1/v2/v3 outcomes.

The PR body reports that the complete A07 output, including frames and protocol data, was retained under ignored path `results-local/doom/map01-v39-live-threat-guard-a07-20261009/` and that a 2,358-entry manifest was verified at the time. That directory was not found at the corresponding path in the current checkout or any of the 15 registered worktree roots checked on 2026-10-19. This transfer therefore preserves only the complete Git-tracked packet; current custody of the external raw bundle is unknown, and this review does not independently reverify those 2,358 files.

The sole non-research PR change adds an A09 summary to `docs/CURRENT_GOAL.md`. It belongs to the separate #8749 allocation, which is already indexed as a distinct A09 packet; it is not part of the A03–A07 evidence transfer. Keep those histories separate. Issue #59 remains open for the integrated live-control question.

This custody review executes no candidate, audit, test, model, game, VM, or allocation. It preserves the 41 research files byte-for-byte and does not promote the scoped custody reconciliation to end-to-end success.
