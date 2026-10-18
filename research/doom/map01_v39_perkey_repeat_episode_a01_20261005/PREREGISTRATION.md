# V39 repeated same-key episode construction A01

## H / T / D / C / U

- **H:** The current one-pair V39 consumer cannot preserve two same-key episodes in one action context; a consumer keyed by the existing unique adapter `actuation_id` can preserve each episode independently while rejecting ambiguous/incomplete pairs.
- **T:** Build one deterministic four-row CPU fixture from the retained fake-display F8 down/up pair in consumer A03. Duplicate the pair with all timestamp brackets shifted by exactly 1,000,000 ns and a distinct `actuation_id`; retain action id, step, owner, intent token, and key. Run the baseline consumer once against the four-row input, run the successor candidate once, and independently reconstruct from raw rows.
- **D:** `PASS_MULTI_EPISODE_CONSTRUCTION_SCOPED` only if the baseline refuses the multi-episode stream, the candidate and independent auditor reconstruct exactly two ordered non-overlapping F8 episodes with distinct actuation IDs and identical outer context, and authority/effect remain false. Otherwise retain FAIL/STOP as observed. Mutation tests must refuse duplicate actuation identity, missing edge, mixed context, and overlap.
- **C:** Main is frozen at `40f15b8b04fbdc33327fd18d52250930fb03aee1`; baseline source is the checked-in A03 consumer. CPU-only deterministic fixture derived from retained fake-display rows; no OS input or shared resource.
- **U:** Does not establish production integration, keymap/physical occupancy, application consumption, useful feedback, live threat response, bounded latency, recovery, MAP01 completion, or human-tempo benefit. This is only an identity/join construction discriminator.

The experiment is single-run. No retries or changes to predecessor evidence. Input and source hashes will be frozen before the baseline/candidate/auditor executions.
