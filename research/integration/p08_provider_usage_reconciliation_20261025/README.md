# P08 provider-usage reconciliation

This audit independently reconciles the one P08 model turn across the retained
App Server protocol, provider-call result, and all-attempt ledger. It also
checks that the exact saved point is the protocol's completed answer and that
the original run SHA-256 manifest remains valid.

Run `py -3.13 research/integration/p08_provider_usage_reconciliation_20261025/audit.py`.
The result is scoped to one stale-generation refusal on synthetic Fake X; it is
not an efficiency comparison or reliability estimate.
