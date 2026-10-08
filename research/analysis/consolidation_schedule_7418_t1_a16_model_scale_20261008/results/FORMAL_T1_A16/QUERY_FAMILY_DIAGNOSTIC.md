# A16 posthoc query-family diagnostic

This descriptive decomposition uses the exact-answer reconstruction from `verify_raw_crosscheck.py`. Each cell is correct/18: the same query type is asked at six prefixes under three seeds. Prefixes reuse the same ledger and are not independent observations; this is not an inferential test.

| Query family | episodic-only | per-episode | batch-2 | terminal |
|---|---:|---:|---:|---:|
| Common save effect | 15/18 | 3/18 | 9/18 | 3/18 |
| Rare forbidden-effect exception | 9/18 | 9/18 | 11/18 | 6/18 |
| Conflicting revision fact | 18/18 | 18/18 | 15/18 | 12/18 |
| History delta | 12/18 | 12/18 | 18/18 | 18/18 |
| Held-out conjunction | 18/18 | 18/18 | 18/18 | 18/18 |

The aggregate schedule differences are heterogeneous. Episodic-only's 12-answer lead over per-episode across 90 responses comes entirely from the common-save query (15 vs 3); the other four query types tie. Episodic-only's 15-answer lead over terminal combines common-save (+12), conflict (+6), and rare-exception (+3), partly offset by terminal's history-delta advantage (-6). Batch-2's 11-answer lead over per-episode combines common-save (+6), rare exception (+2), and history delta (+6), offset by conflict (-3). Batch-2's 14-answer lead over terminal comes from common-save (+6), rare exception (+5), and conflict (+3); history and conjunction tie.

Thus the registered aggregate cadence contrast is present on this query mixture, but it is not a uniform benefit across task types. The held-out conjunction has no discriminating power here (18/18 for every schedule). Each family has only one hand-authored query repeated across prefixes/seeds, so broader task-family generalization remains untested. This qualifies A16's scoped result; it does not invalidate the formal audit or add new seeds. See `INDEPENDENT_CROSSCHECK.json` for the machine-readable counts and `verify_raw_crosscheck.py` for the reproducible calculation.
