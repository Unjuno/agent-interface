# Formal result — Issue #2107 held-out GTK release-decision route

Allocation: `issue2107-gtk-release-decision-formal-01-20260927`  
Public preregistration: [PR #4595](https://github.com/Unjuno/agent-interface/pull/4595)  
Frozen source commit: `97c0da05c880fe047902d5bce8bb889df2b52f4e`  
Main base: `92596bfb750be63c03d3d2906a05d5a5933651c2`  
Container: `sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba` (`linux/amd64`)

## Disposition

**`HOLD_NO_DECISION_VALUE`**. All preregistered safety/correctness gates passed, but the v11 interval receipt did not improve the frozen decision-path metrics over the v10 synchronous release-call return. This is a scoped result for one deterministic policy and one synthetic GTK route. It does not satisfy the broader Issue #2107 acceptance; keep the issue open.

## Execution and audit

- One formal Docker invocation; 56/56 fresh GTK/Xvfb cases completed; zero formal reruns.
- Conditions: 16 `NO_RELEASE_RECEIPT`, 16 `VALID_RELEASE_RECEIPT`, 16 `AMBIGUOUS_RECEIPT`, and 8 `CONTRADICTORY_EFFECT` rows.
- The independent standard-library auditor ran in a separate `--network none --read-only` Docker invocation against read-only raw evidence. It returned `HOLD_NO_DECISION_VALUE`, `errors: []`, with 16 pairs.
- Terminal decisions matched the control contract: all 16 NO-receipt, 16 valid-receipt, and 16 ambiguous-receipt effect-present rows ended `CONTINUE`; all 8 no-effect/contradictory rows ended `ABORT`. No release receipt was treated as application-effect authority.
- The runner recorded zero model calls, provider calls, and tokens. The environment was synthetic and offline.

### Post-run independent metric recheck

After review, two aggregation/gate issues were found in the frozen original auditor: its reported `0.818%` compared the two arm medians rather than taking the median of the 16 paired relative changes, and its PASS logic did not enforce the preregistered ≥20% action-reduction threshold. The frozen source and original `AUDIT.json` remain unchanged. A separate post-hoc script recomputed paired metrics directly from the retained 56 raw rows; it is not a formal rerun.

- Correct median paired relative latency reduction: **−0.828%** (a slight worsening, not an improvement). The paired-bootstrap 95% interval is **−10.78% to +5.05%**.
- Median absolute latency reduction remains **−1,738,179 ns**; the 95% interval remains **−5,979,677 to +5,333,551 ns**.
- Median action reduction is **0%**, with interval **[0%, 0%]**. The explicit ≥20% median action and positive-lower-bound gates both fail.
- Corrected disposition remains **`HOLD_NO_DECISION_VALUE`**. The evidence supports neither preregistered benefit threshold.
- Recheck implementation and machine-readable report: `paired_metric_recheck.py`, `test_paired_metric_recheck.py`, and `evidence/audit-formal01/PAIRED_METRIC_RECHECK.json`.

This correction supersedes only the latency aggregation and action-gate interpretation above; it does not alter frozen inputs, raw evidence, or the HOLD disposition. Do not cite the original 0.818% as a paired effect.

## Decision-value metrics

- Paired median caller-return-to-correct-decision latency reduction for VALID vs NO receipt: **0.818%** (about 0.82%), below the preregistered 20% threshold. The 95% paired-bootstrap interval for absolute latency reduction was **−5,979,677 to +5,333,551 ns**, spanning zero.
- Median reduction in policy `WAIT`/`QUERY`/`RETRY` actions: **0**; paired-bootstrap 95% interval **[0, 0]**.
- Median v11 receipt-RPC duration overhead vs v10 release call: **64,418 ns**; paired-bootstrap 95% interval **−58,600 to +150,500 ns**. The interval spans zero; do not interpret this small-block estimate as a stable cost measurement.

The evidence therefore supports neither the preregistered ≥20% latency reduction nor an action-count reduction. The receipt's extra instrumentation has no demonstrated decision value in this route; the registered result is HOLD, not a general proof of no value.

## Artifacts and scope limits

- Raw formal rows, XWD images, app/key events, receipts, traces, and cleanup: `evidence/packed/formal01.zip`; extract as described in `ARCHIVES.md` to restore `evidence/formal01/`.
- Independent report: `evidence/audit-formal01/AUDIT.json`.
