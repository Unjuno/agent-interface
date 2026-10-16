 #3108 physical GTK release timing allocation
Date: 2026-09-20 Asia/Tokyo
Image: agent-interface-2994:20260920; digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c
Network: disabled; fresh container; working directory /workspace.
Command: python3 /run/audit_run.py
Pre-registered deadline: 2,000,000,000 ns (2 seconds) from execution started_ns to first release receipt.
Result: PASS_PHYSICAL_RELEASE_TIMING_SCOPED; runner exit 0.
Emitting cases useful/no_effect/partial/cleanup_failure: all release_verified true, keys_down/buttons_down empty, latencies 111857532/107500206/109513061/112927000 ns. Non-emitting cases had no release receipt and remained YIELD/refusal paths.
Source hash audit_run.py: pending bundle hash recorded by GitHub file; image digest above. Model/network calls 0/0.
Boundary: one GTK/X11 fixture allocation; no broad safety deadline, model, or production claim.
