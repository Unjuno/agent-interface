# P10 preregistration — matched direct-input / compiled-caller efficiency

This is a new, preregistered six-cell comparison on deterministic synthetic Fake X. P09 remains immutable; P10 uses a separate runner, raw root, and trial identities.

## Question

Under the same model-grounded observation and target task, how do `interface_guarded_input` and `interface_guarded_compiled` compare for exact independent task effect, verified release, provider-reported usage, and caller wall time?

## Conditions fixed before provider calls

- Six cells in three counterbalanced pairs, in the exact order in `RUN-ORDER.txt`: direct/compiled, compiled/direct, direct/compiled. One fresh process/session and one provider generation per cell. No retries, replacements, recovery, or pair reordering.
- Runtime source is current main `b62eed22eda49c7f76813930492c53326fd45391`. Use Windows CPython 3.13, `RecordedPublicMcpCaller`, and a child-owned deterministic Fake X transport. Both arms use the same public observation, exact screenshot bytes, prompt, two-integer output schema, mint path, synthetic target, independent effect oracle, model `gpt-6.1-sol`, and effort `low`; only the final public action route differs.
- The model receives the exact public observation image. The screenshot contains three small colored labeled targets; the prompt asks for the green target and supplies no coordinates, alias, or action payload. The model-derived point must mint against that observation sequence. One direct cell uses public guarded input; one compiled cell uses the preregistered single-transition compiled caller.
- Independent success requires the exact selected point to match the owner-side click within the green rectangle, exactly one click/effect, expected final pixel, a completed selected route, verified neutral release, a complete provider-attempt ledger, and matching private raw hashes.
- Per-cell endpoints: provider-reported input/output/reasoning tokens; provider-turn duration; observation-to-action-return latency; total trial duration; public tool-call count; compiled transition count. Report raw per-cell results and paired direct-minus-compiled deltas/medians. Keep correctness/release counts separate from costs.
- Preserve every first outcome, including failures and unknowns. A failed outcome is not replaced. Do not aggregate unmatched P09 samples with P10.

## Decision and limits

A cell passes only if the frozen independent effect/release gate and usage/raw-ledger integrity checks pass. Report all six cells, three pairwise deltas, per-arm pass counts, and the exact small-sample reliability limits. App Server protocol/usage and attempt-ledger reconciliation do not independently establish upstream billing or account-level charge; no such source is available in this packet. Three pairs are exploratory descriptive evidence, not a broad reliability estimate.

This experiment uses synthetic Fake X only. It does not qualify live GUI control, GZDoom/MAP01, WSLc, physical input, blocked platform-I/O release, cross-domain transfer, or recovery.

## Custody

The private raw originals are local-only under the exact new raw root supplied at launch. Do not modify them after a cell ends. Audit the private originals before export. The repository export omits private binary/raw-ledger contents and retains a hash index; this permits hash comparison but not public reconstruction of raw-attempt reconciliation. Any accidental overwrite, unexpected pre-existing path, or loss of a cell manifest is a custody failure; stop and preserve the affected first outcome.
