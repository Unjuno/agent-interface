# Formal result — T0

**Outcome:** `METHOD_PASS_SCOPED` on the frozen eight-case deterministic fixture. This is not a model, embedding, production-scale, GUI, task-effect, or execution-safety result.

The candidate and independent auditor each ran once in separate network-disabled WSLc containers using the pinned CPython 3.12.14 image. Candidate exit: 0 (`PASS_CANDIDATE_SHAPE`, 8 cases). Auditor exit: 0 (`METHOD_PASS_SCOPED`, 8 cases × 3 methods, no errors). Formal retries: 0. The raw candidate output and auditor JSON are preserved unmodified alongside this report.

With `k=2` and widening budget 6, fixed top-k then hard filtering selected eligible skills at ranks 1 and 2, but returned no card for eligible skills at ranks 3 and 6. It correctly represented these partial-search misses as `UNKNOWN_NOT_FOUND_WITHIN_BUDGET`. Exact filter-then-rank selected known eligible skills across the fixture after scanning all 7 records. Bounded widening selected the eligible skill at rank 6 after 6 metadata checks; it did not find rank 7 and returned `UNKNOWN_NOT_FOUND_WITHIN_BUDGET`. On a fully scanned all-ineligible registry it returned `NONE_PROVEN_APPLICABLE`. Unknown applicability never became a selected candidate; unresolved-only cases remained UNKNOWN. No non-ALLOW skill was selected.

This supports only the frozen method-level discriminator: post-filter top-k can starve an eligible item beyond k; widening recovers items within its scan budget and must retain an uncertainty status beyond that budget. Synthetic authored ranks do not measure embedding recall, real-world applicability truth, latency/tokens, registry economics, or downstream task outcomes. No deployment or runtime-promotion claim follows.

WSLc warned on both formal invocations that the kernel lacks swap-limit capabilities or the cgroup is not mounted. One CPU was requested; the 512 MiB memory ceiling is not claimed as enforced. No GPU, network, pull, model, GUI, or external side effect was used.

See `PREREGISTRATION.md`, `FREEZE.json`, `RUN.json`, `CONSTRUCTION.md`, and `SHA256SUMS.txt` for protocol and provenance.

