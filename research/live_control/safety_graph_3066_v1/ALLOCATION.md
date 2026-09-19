 #3066 runtime safety fault allocation
Date: 2026-09-20 Asia/Tokyo
Image: agent-interface-2994:20260920; digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c
Network: disabled; fresh container.
Scope: runtime X11RuntimeSession with a declared fake-backend fault fixture; not a physical actuator claim.
Schedules: normal, execute fault, release-unverified fault, stale observation.
Result: PASS_SAFETY_GRAPH_RUNTIME_RECONCILIATION_SCOPED. Normal completed with verified release; execute fault returned BACKEND_EXECUTION_FAILED and recovery_required; release fault returned release_unverified and recovery_required; stale was refused before emission. Observed dependencies were all within declared graph. Model/network calls 0/0.
Source hash: 5a420551a1d96565e16c3eb8ac038c8e181b279a911b0427bd2bc15193babed7
Result hash: e9d75940424c66b1109180b403ec4f0381714f5f3b7ccdc4fafc7655edf914b1
Boundary: fake backend/runtime session fault contract only; no physical timing deadline, actuator residual-state, or broad safety claim.
