# Role-skill lifecycle amortization — current-main successor allocation

Successor allocation for Issue #5084. The preceding `larger_rung_v1` freeze
and its stale-main history are preserved unchanged. Before any container was
started, this allocation's first pre-run freeze (`7da55b73…`) was refreshed
from main `821482e` to `9d91450`; the previous digest is retained in
`FREEZE.json`. The main advancement was unrelated, and all five candidate,
both reference and both input hashes remain unchanged. No experiment result
is implied by this preparation.

The frozen one-shot design is 15 paired alternating AB/BA blocks, 1,000
requests per arm per block, exact prediction reconciliation, and a separate
raw-only audit. See `FREEZE.json` for commands, limits, decision thresholds,
and source/input identities. Scope remains synthetic single-seed
pure-Python lifecycle behavior only.
