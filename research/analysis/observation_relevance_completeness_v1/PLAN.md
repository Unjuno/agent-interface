# #1726 O3 relevance completeness provenance

H: exact current relevance-generation + intent-epoch does not prove the declared relevance set is complete. Useful suppression outside the declared ROI is universally safe only when completeness is guaranteed by trusted provenance or construction.

T: exhaustive six-tile state space: all 64 true relevance sets, all 64 declared sets, six changed tiles, critical none/{x}; 49,152 rows. Compare ASSUME_COMPLETE, truthful COMPLETE_ONLY, forged completeness, PARTIAL/UNKNOWN fail-open, and stale-currentness. Independent audit derives closed-form counts. One formal invocation, reruns/replacements/tuning0.

D: unsafe false suppressions6144; truthful COMPLETE_ONLY false suppressions0; safe suppressions192; PARTIAL/UNKNOWN suppressions0; forged complete false suppressions6144; stale suppressions0; analytic witness and corruption/source integrity pass.

C: completeness may be guaranteed by an interaction ISA/task compiler instead of an explicit field. Heuristic/model completeness claims require trusted provenance.

U: synthetic exact semantics only; no real relevance inference, GUI, token, latency, task or ABI claim.
