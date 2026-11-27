# P07 provider and score reconciliation follow-up

This additive audit reconciles P07's provider accounting across three retained
sources: the App Server `thread/tokenUsage/updated` event, the provider-call
result, and the all-attempt ledger's model-attempt receipt. It also makes the
score disagreement explicit: the frozen runner and initial ledger both record
`task_success=false`, while the separate owner click/effect/pixel and release
receipts support a later post-hoc score of true. Neither raw record is edited;
runtime `task_success` remains null.

Run `py -3.13 research/integration/p07_ledger_rescore_reconciliation_20261025/audit.py`.
`PASS_SCOPED` requires one completed model turn; exact usage agreement across
protocol, provider and ledger; the point/mint/click/effect chain; both release
receipts; and all run raw hashes. This is one synthetic Fake X composition
sample, not a matched efficiency or reliability result and not WSLc/live GUI
transfer evidence.
