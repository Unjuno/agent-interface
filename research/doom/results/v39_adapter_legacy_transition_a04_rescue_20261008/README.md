# Legacy release-transition adapter row — A04

## H / T / D / C / U

**H.** A legacy `input_release_transition` row with nested V39 adapter UP evidence must not be ignored while a separate `input_release_measurement` UP row keeps its adapter intervals paired.

**T.** Pin the exact A03 fixed projector at commit `46bed14701c6ba7d509c620bf6f582c84993f949` and the retained A01 raw edge pair. Run the established identical/conflicting duplicate matrix plus two legacy-transition mutations: duplicate UP under the legacy outer event, and replacement-only UP under that event. Compare baseline and candidate.

**D.** Baseline is expected to fail the duplicate-transition case by returning paired adapter intervals. Candidate must pass both targeted tests; both transition mutations must yield one incomplete adapter receipt with null timing. The ordinary exact-duplicate matrix must remain closed.

**C.** The result JSON records exact source, test, fixture and baseline hashes and captured baseline/candidate test output. The independent auditor derives fixture identity and verifies expected red/green outcomes from that saved output.

**U.** One synthetic retained X-adapter event pair and deterministic projection only. No live X-server, physical dwell, application consumption, task effect, threat response, recovery or MAP01 result is established.

The pinned WSLc command uses the cached Python 3.12 image, `--pull never`, network disabled, one CPU, 512 MiB requested memory, UID/GID 1000, read-only source and distinct output. Host warnings are retained; memory/swap enforcement is not assumed.
