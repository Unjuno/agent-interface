# Result — #1228 subprocess actor provenance

Decision: **PASS_MUTATION_ACTOR_SUBPROCESS_PROVENANCE_SCOPED**.

- Formal invocation: 1; reruns/replacements/tuning: 0
- Transports: fsynced append-only JSONL and Unix socketpair
- Records: 2,000 (1,000 per transport)
- Fresh child processes: 1,778; cleaned: 1,778
- Candidate / independently reduced oracle mismatches: 0
- Lineage-bound non-self false credit: 0
- 500 ms temporal-nearest false self-credit: 1,554
- Authority promotions: 0
- Task-success promotions: 0
- Aggregate/source audit: PASS
- Formal record digest: `690af9cc1b538fa8025f93acdf54a7058eafd6362f9060fbe6d95ca375fb8b9e`

The Python 3.13 environment emitted the frozen `os.fork()` multi-thread warning. No child cleanup loss or deadlock occurred in the formal block. This result establishes only local IPC provenance mechanics. HUMAN/OS are controlled injector labels, not authenticated real-human or kernel actor detection.
