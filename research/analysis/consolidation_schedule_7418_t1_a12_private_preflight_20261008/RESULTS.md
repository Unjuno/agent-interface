# A12 results — FAIL_METHOD

The frozen candidate completed the single authorized run: 390/390 model calls (360 queries and 30 consolidations), exit 0, no retries. Every request retained the frozen model identity; the dedicated API/store preflight passed. The frozen raw-only auditor also exited 0 as a process and returned `FAIL_METHOD` with 18 transition errors. The preregistered method gate failed, so no cadence endpoint is interpreted.

The 18 errors comprise two repeated failure patterns:

- For all three seeds, `per_episode` emitted the exception episode with kind `rare_exception` instead of the required `forbidden_effect_exception` at prefixes 3–6 (12 violations).
- For all three seeds, the final `batch_2` transition omitted the required conflict claim, producing both a coverage error and an explicit-conflict mismatch (6 violations).

Exact-answer accuracy was identical across seeds: episodic-only 0.2667, per-episode 0.5333, batch-2 0.6000, terminal 0.6667. Four pairwise contrasts met the preregistered numerical threshold and direction. These values are descriptive only because the transition gate failed; they do not establish schedule sensitivity under faithful memory transitions.

## Preserved artifacts

- Raw: `results/FORMAL_T1_A12/RAW.jsonl`, 1,987,612 bytes, SHA-256 `ced175c72319de8c2322aaf28c81afb4f21545cc946efa3d5c3a000c405152fc`.
- Audit: `results/FORMAL_T1_A12/AUDIT.json`, 7,785 bytes, SHA-256 `43eaf61fd54fd19b7bc344ab0ff65064d6ab8fcf89778a75c7e8b804248f92bc`.
- Preflight: `results/FORMAL_T1_A12/PREFLIGHT.json`, 1,345 bytes, SHA-256 `d703d3530504d3a194e63fc28b55713ff149be22cc8b460fcaad6c1f86a3cb7d`.
- Candidate and auditor stdout/stderr are saved beside them; both stderr files are empty.

The model, prompt, input, seed, and auditor artifacts remain unchanged. This consumed allocation will not be rerun or repaired. Any successor requires a fresh allocation and fresh seeds.
