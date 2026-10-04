# MAP01 held-input occupancy: conservative early-release successor

This local v2 successor records three fail-closed boundaries against the V7 early-release implementation merged in PR #7346:

1. **Asynchronous release lower bound.** The reproduced single-key trace has first admission 11 ms, first ACK 12 ms, a capture at 30 ms, a verified empty `focus_changed` release record at 40 ms, and later captures at 80/90 ms. Because the owner releases and synchronizes before recording `verified_ns`, the earlier 30 ms capture may already be post-release. V7 candidate and raw auditor both accept an 18–29 ms interval; the defensible interval is 0–29 ms. Frozen v4 reports 68–79 ms.
2. **Step-local completion.** If that hold step completed but a later step is cancelled, the final program status is `cancelled`; V7 then skips the completed hold's early-release correction. The successor keys off that hold's own `step_completed` event and still reports 0–29 ms.
3. **Multi-key admission crossing release.** With the second requested key admitted at 50 ms after verified-empty release at 40 ms, V7 candidate and auditor still accept a single 18–29 ms interval, omitting the later occupancy segment. The successor rejects the trace because a one-interval summary cannot represent it soundly.

The v2 raw auditor independently reconstructs these decisions and rejects corrupted V2 output. Five local tests cover the historical V4 error, the V7 async lower-bound overclaim and V7 audit acceptance, later-key rejection, post-release ACK rejection, per-hold completion, and source timestamp ordering.

The immutable v38/v39 traces have no completed early-release case and no changed occupancy bounds. V38 retains 11 holds and 3,048.890–4,039.878 ms aggregate decision occupancy; v39 retains 29 holds and 6,301.200–8,452.733 ms. The independent raw audit passes both. Source, raw-input, and output digests are in `results/manifest.json`; the exact V7 candidate and auditor copied from PR #7346 are hash-bound as dependencies.

This is a posthoc method follow-up, not a live allocation, exact key-up measurement, task-effect result, recovery result, performance improvement, causal result, or MAP01 completion. It is scoped as a successor to merged PR #7346 because it resolves the conservative-boundary findings and rejects a multi-key trace that V7 and its auditor accept.

Run from repository root:

```powershell
python -B -m pytest -q research/doom/map01-held-input-occupancy-early-release-v1/test_early_release.py
python -B research/doom/map01-held-input-occupancy-early-release-v1/run_posthoc.py
```
