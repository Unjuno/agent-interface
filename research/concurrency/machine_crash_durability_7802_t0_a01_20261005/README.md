# Issue #7802 — machine-crash durability T0 model

## H / T / D / C / U

- **H:** A machine-crash durable image can contain an effect without its local receipt, or a receipt without the effect; a safe recovery classifier must return `UNKNOWN_RECONCILE` rather than infer absence/completion or authorize retry from the local receipt alone.
- **T:** Enumerate five finite protocols: effect-before-receipt across stores, receipt-before-effect across stores, same-transaction atomic commit, effect commit before acknowledgment/receipt, and one untrusted/corrupt-record control. Independently classify all durable images; retain the candidate output and auditor output.
- **D:** `PASS_METHOD_SCOPED` when all 15 enumerated images match the independent oracle and no image authorizes retry; a false classification, retry, or audit disagreement is `FAIL`. This T0 cannot earn the Issue's T1 `H_PASS_SCOPED`.
- **C:** A declared filesystem/database protocol may constrain images more strongly than this finite model. An application effect and local receipt are not generally one atomic transaction; their actual durability domains and commit boundaries are unknown here.
- **U:** Abstract Boolean persistence flags only. No SQLite/VFS, host filesystem, VM, abrupt shutdown, physical media, live external effect, or product recovery was tested. No power-loss durability claim follows.

## Result

The candidate and independent auditor agreed on all 15 model images. Separated-store cutpoints produced both effect-only and receipt-only states, classified `UNKNOWN_RECONCILE`; the same-transaction protocol had only neither/both states in this model. The corrupt control classified `CORRUPT_OR_UNTRUSTED`. Every row had retry authority false. Result: `PASS_METHOD_SCOPED` for this finite model only.

This is a method/model result, not evidence that a supported storage stack actually permits any listed image. T1 remains `HOLD` until a disposable VM, pinned filesystem/storage stack, and validated abrupt-poweroff harness are available.

Run the saved candidate and auditor with the commands in `COMMANDS.txt`; focused local checks are in `TESTS.txt`.
