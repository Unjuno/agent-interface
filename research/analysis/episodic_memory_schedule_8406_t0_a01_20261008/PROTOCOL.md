# Frozen H / T / D / C / U — Issue #8406 T0 A01

**H.** For one exact immutable twelve-episode ledger, the four update schedules will produce the preregistered update checkpoints and source-availability snapshots at the same prefixes. The auditor will detect provenance loss, exception omission, conflict collapse, source mutation, and prefix misalignment. This T0 does not test whether a model's semantic memory changes with cadence.

**T.** Read the exact parent #7418 `fixture.json` at the pinned path/hash. Each arm receives that same episode order and exact content. Build four schedules: no derived writes (episodic-only), one lossless ID+content-hash manifest after every episode, one after each four-episode batch, and one only after episode 12. Retain every intermediate update. At prefixes 3, 6, 9, and 12, run the same source-availability lookup for `heldout-04`, `protected-heldout`, `contradictory`, and `unrepresented`, using only source IDs pinned by the parent's applicability oracle. Record visibility only; emit no answer or inferred claim. The independent raw-only auditor reconstructs the full trace and challenges its validator with five frozen corruptions.

**D.** `PASS_METHOD_SCOPED_T0` only if all twelve source IDs and source-content hashes are identical across arms; update counts equal 0/12/3/1; each arm has 16 query-visibility rows; source availability matches the latest committed prefix; no answer/action/authority appears; the independent audit reconstructs every row; and all five corruptions are rejected. Otherwise retain the first FAIL/STOP and do not rerun.

**C.** Lossless manifests test schedule plumbing, not semantic consolidation; this fixture may show only deterministic exposure differences. An order-sensitive lossy transformation or LLM writer could behave differently, but inserting one here would predetermine the behavior under test.

**U.** No stochastic model, held-out model answer, GUI, task effect, deployed memory, user data, token/cost, safety, or optimal cadence claim. The parent fixture's source truth and predicate vocabulary are stipulated. Query visibility is an exact-source index, not evidence that an agent would retrieve or use those sources.

## Custody and commands

- Main/source commit: `a0d0602b89b1f5a05f851728fe90684ec4bfeff5`.
- Parent fixture: `research/analysis/exception_preserving_skill_7418_t0_20261004/fixture.json`, SHA-256 `1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb`.
- Pre-formal construction tests: `python -m unittest discover -s research/analysis/episodic_memory_schedule_8406_t0_a01_20261008 -v` — 3 passed.
- One candidate: `python research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/candidate.py research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/formal_01/RAW.json`.
- One independent audit: `python research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/audit.py research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/formal_01/RAW.json research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/formal_01/AUDIT.json`.
- Host CPython 3.12.13, standard library only; no network access is used by the protocol. No container was started: this no-model method contract needs no external runtime, and the same host's OrbStack content-store limitation is already documented in contemporaneous repository STOP/preflight records. This result makes no container-isolation claim.
- Invocation counts freeze at candidate 1, auditor 1, retries 0. Candidate/audit outputs are exclusive-create artifacts. Preserve any first failure exactly.
