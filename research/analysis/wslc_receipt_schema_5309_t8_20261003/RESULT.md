# Result — #5309 retained WSLc receipt T8

**Disposition: `PASS_RETAINED_RECEIPT_SCHEMA_AUDIT`.** The single frozen offline validator accepted the exact 306-byte stdout artifact retained by T7 and confirmed the preregistered 432-row receipt values. This validates that captured receipt only. T7's formal `STOP_HOST_RECEIPT_SCHEMA_MISMATCH` remains unchanged.

- Successor Issue: [#6990](https://github.com/Unjuno/agent-interface/issues/6990).
- Lineage: [#6975](https://github.com/Unjuno/agent-interface/issues/6975), [#5309](https://github.com/Unjuno/agent-interface/issues/5309), retained in [draft PR #6983](https://github.com/Unjuno/agent-interface/pull/6983).
- Allocation: `WSLC-RECEIPT-5309-T8-20261003-01`.
- Frozen protocol commit: `101bee219d926dcbe8da04a06696a15210261b48`.
- Input Git blob: `588d1816282ab17790faa3a94a939f9fce8d8bc3`; 306 bytes; SHA-256 `604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f`.

The one CLI validation exited 0 and emitted `formal_validation.json`. Its strict schema and exact-value checks confirmed **432/432** rows, **432** unique cases, **432** independent row matches, semantic SHA-256 `a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193`, wrong-target counts **27** for task fallback and **0** for yield fallback, zero authority grants, and an empty error list. The T7 host verifier expected `failed_probe_yield_fallback_wrong_target`, while the unchanged captured auditor receipt uses `failed_probe_yield_wrong_target`; T8 records this schema mismatch but does not repair or relabel T7.

The 7/7 construction/mutation suite rejected changed input identity, field set/name, row count, status, non-empty errors, and a boolean masquerading as an integer. Candidate runs: **0**; WSLc runs: **0**; Docker runs: **0**; retries: **0**. No timing or memory measurement was made.

## H / T / D / C / U

- **H:** Supported for the retained receipt bytes only: the payload is valid JSON matching the frozen key set, exact counts/digest/status, and no-error/no-authority conditions.
- **T:** One standard-library host CLI validation after the freeze; no container, network, candidate, source auditor, or retry.
- **D:** `PASS_RETAINED_RECEIPT_SCHEMA_AUDIT`: exact input length/hash passed, the strict value checks passed, the one output receipt was retained, and all seven construction/mutation tests passed.
- **C:** This is a post-hoc offline validation, not a rerun of T7 and not an independent re-execution of the 432-row T6 auditor. It explains why the already captured result failed T7's separately frozen host-verifier schema gate.
- **U:** Does not revise T7 STOP or T6, establish runtime portability/performance/memory benefit, compare Docker or WSL runtimes, or support a live GUI/model/application/safety claim.
