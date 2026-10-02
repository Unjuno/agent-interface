# #6256 T2 comparator/cost analysis — retained HOLD

**Disposition: `HOLD_COMPARATOR_ASSERTIONS_INVALID`.** One formal invocation returned `FAIL_OR_HOLD`, exit 0, with two failed assertions. Do not interpret that status as evidence against backward derivation: both assertions were about the analysis harness's comparator semantics, not unsafe admission by the frozen guard. The raw structured transcription below is not byte-exact stdout capture; the original complete output remains in the conversation/tool record.

## Independently visible facts in the output

- Input model/candidate hashes matched the pre-run freeze.
- Exact universal preimage and candidate preimage matched: `ready_complex`, `ready_simple`, `unobservable_safe_alias`.
- Exhaustive forward enumeration covered all 10 states / 13 outcomes and yielded exactly that same preimage.
- The supposed proposal-local comparator read the candidate's complete per-outcome rows for all 10 states; it therefore admitted exactly the preimage. Its equality is expected for this fully enumerated fixture and does not demonstrate a weaker comparator.
- The pixel-only decision output grouped more than two states. The check incorrectly required an exact group equal to `{ready_simple, already_committed}`; `pixel_alias_not_unknown` was therefore a bad assertion. A proper check asks whether that pair shares an observation signature while having different oracle labels.
- The illustrative ordinal-cost enumeration emitted one feasible cue set/frontier row. It supplies no measured latency, token, or risk cost and no evidence that weights reverse a choice. The T2 planned weight-sensitivity conclusion was not established.

## Scope and preservation

This deterministic CPU analysis used the frozen synthetic fixture only; candidate/runtime/model/GUI/network/external-action/OS-input invocations were all zero. Docker Desktop service was stopped and the CLI did not respond; no Docker state was changed. T0 #6276 remains `HOLD_INCOMPLETE_MUTATION_COVERAGE`; T1 #6277 remains a scoped mutation-coverage PASS. Neither is revised by T2.

The next step is the audit-only successor #6285, with independently specified comparisons: exact proposed-guard validation over its admitted states; all-state forward enumeration; and observation partitions checked by mixed oracle labels, not an exact expected group size. No T2 rerun or posthoc source repair is permitted.
