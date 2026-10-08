# X11 timestamp-order allocation v2 — complete case ledger, formal receipt HOLD

Allocation: `x11-timestamp-order-20260923-02`. Issue #4220.

## Disposition

- Formal invocation: **1**, reruns/replacements/tuning: **0**.
- `run_v2.py` completed **24/24** frozen cases; all case return codes0, no case timeout.
- Independent raw-only audit on a byte-preserving audit copy: **PASS**, errors=[]; 12/12 corruption controls rejected.
- Frozen scientific discriminator is present: AB_BURST ties4/4, BA_BURST ties4/4, BAB_BURST ties4/4; co-timestamp false ordered-prefix satisfactions12 across8 cases; strict-time disagreements in8 cases.
- Raw-row scientific decision: **PASS_X11_TIMESTAMP_ORDER_BOUNDARY_SCOPED**.
- **Formal acceptance remains HOLD_OUTER_EXECUTION_RECEIPT_MISSING** because the outer tool envelope killed `execute_v2.py` before it wrote `EXECUTION.json`. The already-running `run_v2.py` continued as the same invocation and completed, but its process exit status cannot now be recovered. No exit is inferred from `RUN.json` or absence in `/proc`.

This separation follows repository failure routing: successful raw reconstruction cannot invent a missing process exit. The earlier allocation-01 STOP remains unchanged.

## Frozen scientific result

The complete ledger confirms the intended semantic separation:

1. Co-timestamp semantics can satisfy B-before-A when B and A share the same X server tick. BA_BURST shows this in 4/4 cases; ordered semantics expires.
2. Strictly-greater timestamp semantics misses valid later B events when A and B share one tick. AB_BURST and BAB_BURST expose this.
3. Local channel ordinal preserves the tested later-event relation while retaining the same 80 ms source-tick deadline.

This does not falsify #1764, which intentionally defines same-timestamp fragments as unordered co-occurrence. It also does not establish causality, stream completeness, semantic application completion, model/task utility, production safety or cross-backend behavior.

## Evidence integrity

Freeze SHA256: `4c66066a900b1017268b9ef4f693c31aa71039c1eae3afce4119c68595db4581`.
Raw audit SHA256: `7c60c64b0c12d5514ef86243e4e7f8b02721dab79c2d306375dd480d36dd5680`.
Run ledger SHA256: `147bba0d3761b26ca0717d9403fc3a6a3894196eb2cb581b387ca2746344e1d6`.
Acceptance record SHA256: `bc5fa33269ceee7245fff901131d1fc014ff93682741c6db39883ed44b85ff54`.

Audit wrapper incident retained: the original auditor hard-coded `FREEZE.json` while v2 used `FREEZE_V2.json`. Its first invocation failed with FileNotFoundError before reading rows. A separate audit-only copy aliases the exact freeze bytes to the expected filename; no formal raw/source row changed.

## Integration decision

For a runtime contract, explicitly select one of: same-timestamp co-occurrence, later event on a declared ordered channel, or independently evidenced causal application completion. Do not infer channel order from server-timestamp strict inequality, and do not infer causality from the local ordinal.

No production adapter is promoted from this allocation while the formal outer receipt gate is unresolved. No automatic rerun is authorized.
