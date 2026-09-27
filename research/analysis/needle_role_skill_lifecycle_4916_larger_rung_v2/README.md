# Role-skill lifecycle amortization — current-main successor allocation

Successor allocation for Issue #5084. The preceding `larger_rung_v1` freeze
and its stale-main history are preserved unchanged; this allocation is based
on current main and reuses the same five hash-pinned candidate files and exact
seed-3788 inputs. No experiment result is implied by this preparation.

The frozen one-shot design is 15 paired alternating AB/BA blocks, 1,000
requests per arm per block, exact prediction reconciliation, and a separate
raw-only audit. See `FREEZE.json` for commands, limits, decision thresholds,
and source/input identities. Scope remains synthetic single-seed
pure-Python lifecycle behavior only.
