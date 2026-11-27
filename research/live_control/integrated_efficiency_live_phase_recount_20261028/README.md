# #57 Chromium phase-time recount (2026-10-28)

This additive read-only recount reads the detailed `integrated-efficiency-live-01` report directly from current main commit `52df8e2d934bd8b20d4d36da8a7f17a524c49210`, pinned by report SHA-256 `84672ef551b97764c73ccdf4070b82db043d4e56bc509137e69c057c11aaa7da`. It does not hydrate the large result tree, change or replay the original study, and verifies the retained task identities, exact submissions, verified releases, preflight-inclusive token totals, and planner-generation totals before grouping elapsed time by the preregistered task route.

| Phase | Plain | Persistent | Persistent minus plain | Interpretation |
|---|---:|---:|---:|---|
| Cold acquisition (task 1) | 9.410 s | 11.025 s | +1.615 s | Persistent is slower in the first task |
| Warm layout A (tasks 2–3) | 17.930 s | 8.232 s | −9.698 s | Reuse offsets cold overhead |
| Invalidation and repair (task 4) | 9.127 s | 12.341 s | +3.214 s | Repair is slower than plain cold acquisition |
| Warm after repair (tasks 5–6) | 19.945 s | 12.533 s | −7.412 s | Reuse recovers part of repair cost |
| **Six tasks total** | **56.412 s** | **44.131 s** | **−12.281 s** | **21.8% less elapsed in this sequence** |

The speed difference is therefore carried by reuse tasks, while the cold and repair costs are losses. The two warm ranges save 17.110 s in total; cold acquisition and repair add 4.829 s, yielding the reported 12.281 s net difference. The report also records 63,128 versus 26,563 cumulative input tokens including preflight, and 6 versus 2 image-model task calls after the separately charged preflight.

This remains one fixed six-task sequence per arm. It cannot estimate a general speedup or reliability rate, and this recount is arithmetic over the detailed report rather than an independent raw-event audit. The separate aggregate-only Docker summary remains unreconciled and is not pooled here.

Reproduce with `python recount.py`; the script writes only sibling `recount.json`. It refuses any change to the pinned source report or to its required exact-submission/release/route/accounting gates.
