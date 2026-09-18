# #1820 REVEAL support-closure composition

H: #689 target-crop feedback is not by itself a complete O3 support set because CONTEXT_READY also depends on global target uniqueness. A crop can remain byte-identical while a duplicate target appears outside it. Re-evaluating global uniqueness locally on the exact current source should make crop reuse safe without forcing full-current model escalation on irrelevant outside changes.

T: 12-tile synthetic source; two-tile fixed crop and ten outside tiles. Exhaust 3^10 outside mutation patterns {unchanged, irrelevant change, duplicate target} × critical flag × source-current flag = 236,196 rows. CROP_ONLY vs CROP_PLUS_GLOBAL_UNIQUENESS. Directed target-removal/signature/stale/critical/unbound-uniqueness controls. One formal invocation; reruns/replacements/tuning0.

D: baseline false suppressions58,025; candidate false suppressions0; candidate safe reuses1,024; ambiguity raw fallbacks58,025; current critical forwards59,049; stale-source fallback118,098; analytic witness and independent combinatorial audit/corruption/source integrity pass.

C: a trusted complete target index/accessibility source may replace full-pixel scanning. If REVEAL semantics are ROI-local rather than globally unique, the global closure is unnecessarily broad.

U: synthetic contract composition only; no detector accuracy, capture saving, model/token, latency, task or ABI claim.
