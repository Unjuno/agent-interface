# A15 result summary

Status: **FAIL_METHOD**. The single candidate invocation completed all 390 planned calls. Row IDs are contiguous; no call returned an error; all pre/post tags and loaded digests matched the frozen Qwen3:8B digest. The independent transition auditor ran once and returned 24 errors.

Against A14, the typed conflict clarification removed the false `conflict:exact_effect` coverage failures seen at four per-episode prefixes across the three seeds (12 errors). However, A15 introduced a wrong rare-exception effect (`draft_saved` substituted for `no_external_effect`) at all four per-episode checkpoints for every seed (12 errors). The batch-2 premature conflict at prefix 4 and conflict-payload mismatch at prefix 6 persisted in all seeds (9 errors), and the terminal exception-effect error also persisted (3 errors). Total auditor errors were 24 versus A14's 21. The net count rose by 3, with the per-episode failure mode changing.

Per-seed exact answer accuracy is in `audit.json`: episodic-only .2667 for each seed; per-episode .5333/.5333/.5000; batch-2 .6333 for each; terminal .6667 for each. These are descriptive only and do not support schedule conclusions under the preregistered transition gate. No inference is made about GUI use, real user memory, or product effectiveness.

Raw SHA-256: `dee102f3c78340985c9993c3b1c28172a5dbb480d38c72be1fc3e59dfe400fe1`
Audit SHA-256: `078cae511d2d295484a95efb094d0cce3e1158de52cb138318f8bbfbcc38da89`
Preflight SHA-256: `7fe0ab30eea1cf9ecb7b9c6063992ec9904210d348090728c05776117e0d3922`
