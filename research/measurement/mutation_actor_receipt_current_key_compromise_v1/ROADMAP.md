1. Freeze H/T/D/C/U and immutable BASE before implementation.
2. Reserve a machine-visible branch before primary execution.
3. Reconstruct only the minimum #1272 single-root verifier semantics needed for the boundary; do not change acceptance rules.
4. Implement candidate verifier and independently structured hidden-provenance oracle.
5. Run excluded fixed controls only; primary batch IDs remain unused.
6. Freeze exact source, batch schedule and auditor to GitHub; read back and re-check Issue/branch/PR ownership.
7. Execute four immutable 50,000-pair primary batches exactly once each.
8. Aggregate once; independent audit, corruption controls and source rehash only.
9. Publish first outcome and stop; no repair mechanism or live experiment in this allocation.
