# Deterministic postcondition boundary experiment

Issue: #3048

## H/T/D/C/U

- H: known postconditions can be decided deterministically without rich-agent calls, while wrong-target, stale, pixel-only, missing-receipt, and cleanup-failure evidence does not become success.
- T: run a fresh Docker/Xvfb allocation with a real GTK fixture; measure a saved effect digest, an X11 window geometry transition, and a typed saved-state receipt; evaluate negative and incomplete evidence with an independent pure verifier.
- D: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :150, model/network calls 0.
- C: PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED. Three known cases passed; wrong target failed; stale/pixel-only/missing receipt/cleanup failure held unknown. Independent recomputation is the verifier function in run.py.
- U: local three-contract GTK/X11 scope only. No model quality, broad GUI generality, latency/token benefit, or production claim. The verifier contracts must be extended and revalidated per application/effect.

The result preserves fail-closed distinctions and does not convert HOLD or FAIL into success.
