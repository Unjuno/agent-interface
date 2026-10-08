# Issue #5927 — OrbStack container T0 successor

## H / T / D / C / U

- **H:** For the frozen finite task/channel family, transcript-equivalent worlds with disjoint safe-progress actions require a fresh distinguishing exchange; where a shared safe-progress action exists, the lower bound is zero.
- **T:** Exhaustively enumerate the positive save/modal case and null shared-safe-action case using the exact candidate, case input, independent v2 auditor, and construction tests already retained on main. Run the construction gate first, then one candidate invocation and—only on candidate exit 0—one raw-only audit in a separate network-disabled, resource-bounded OrbStack container. No model, GUI, GPU, network, game, OS input, or task effect.
- **D:** `PASS_METHOD_SCOPED` only when the positive case has minimum one exchange (`persistence_receipt`), the null case has minimum zero, and independent reconstruction returns `PASS_RAW_AUDIT` with no errors. Any construction/setup/candidate/audit failure is retained without retry.
- **C:** The worlds, channel table, safe-action oracle, and receipt truth are authored and finite. The container validates execution isolation, not truthfulness of a real persistence receipt.
- **U:** No universal GUI feedback bound, rich-model-call lower bound, live safety/effect, calibrated cost, latency, or production result is established. The unit is one fresh channel exchange only.

## Result

Disposition: **`PASS_METHOD_SCOPED`** for this finite method fixture. The candidate reported a minimum of one fresh `persistence_receipt` exchange for `save-modal-positive` and zero for `shared-safe-inspect-null`. A separately launched raw-only v2 auditor independently reconstructed both cases and returned `PASS_RAW_AUDIT`, errors `[]`. The construction suite passed 8/8. Candidate and auditor each ran once; retries: 0.

The positive witness is scoped to the authored transcript and safe-action table: without a fresh discriminator, the persisted and modal-blocked worlds have no common safe-progress action; the declared receipt separates them. In the null control, `inspect_again` is safe in both worlds, so the checker correctly declines to claim positive feedback necessity.

## Frozen source and execution

The source and `cases.json` are the byte-pinned main-branch files from the host-only predecessor package, read-only mounted into each container. Predecessor allocations 01 and 02, including allocation 01's raw-audit FAIL and allocation 02's host-only PASS, are not modified or replayed. This is a fresh container execution with a new allocation ID and output namespace; it does not upgrade the predecessor results.

The cached `linux/arm64` Python image was pinned by digest. OrbStack Engine 29.4.0 / Docker client 29.5.2 ran each job with networking disabled, 1 CPU, 256 MiB, a read-only root filesystem, a read-only input mount, and a distinct writable output mount. The candidate and auditor ran in separate ephemeral containers. Exact commands, exit codes, output hashes and stdout are in `RUN.json` and the adjacent log files.

## Integrity discrepancy retained

On current main, the predecessor `SHA256SUMS` verifies the frozen `cases.json`, candidate source, auditor source, and both construction-test sources. Four entries for predecessor raw outputs do **not** match their committed bytes. Those four historical artifacts were not inputs to this run, were not altered, and are not represented here as checksum-verified. The new candidate/audit outputs have their own fresh SHA-256 entries. This readback discrepancy does not change either predecessor disposition and should be investigated separately before relying on the predecessor raw-output hashes.

## Scope boundary

This establishes only that this finite enumerator, input, and independent checker agree in the pinned container. It does not establish that the state universe is complete, that real receipts are independent or truthful, that a screenshot/model call is universally necessary, or that one exchange equals any number of bits, bytes, tokens, seconds, or cost. Any live GUI/task-effect rung needs its own allocation and oracle.
