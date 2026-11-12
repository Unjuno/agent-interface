# V40 cancellation release-receipt fault injection (T3, 2026-10-04)

## H / T / D / C / U

**H:** Both initial-admission and renewal invalidation cancellation helpers reject every terminal whose lifecycle is not `cancelled` or whose release is missing, unverified, or reports held input; each sends cancellation for the matching cover, and the renewal path interrupts the matching planner turn.

**T:** Against the exact V40 controller in this checkout, inject one valid empty cancelled terminal and five adverse terminal receipts into each production helper. Record the disposition and emitted cancel/interrupt identifiers, then run an independent audit over the saved result.

**D:** `PASS_CONSTRUCTION_FAULT_INJECTION` only if both valid controls are accepted, all ten adverse receipts raise the helper's fail-closed error, cancellation IDs match, and renewal interruption binds to `turn-t3`. Any adverse acceptance or identifier mismatch fails.

**C:** A real session child and OS input backend may have lifecycle semantics beyond these host-side helper contracts; this cannot establish physical key/button release.

**U:** This is deterministic host-side helper construction. It does not run the child runtime, game, parser, model, GUI, OS input, or formal #59 allocation; it makes no task-effect, survival, or efficacy claim.

## Execution

Run from the repository root:

```powershell
python research/doom/v40_release_receipt_faults_59_t3_20261004/experiment.py
python research/doom/v40_release_receipt_faults_59_t3_20261004/audit.py
```

The first command executes both cancellation helpers against 12 frozen case rows and writes `experiment-result.json`. The second independently checks the matrix, accepted/rejected decisions, and command/interrupt bindings. Raw command output, exit codes, source identity, and hashes are retained beside this report.
