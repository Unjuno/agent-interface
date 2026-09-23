# Session/resource-bound receipt bridge

Issue: #3167, successor to #2977/#1924.

## H/T/D/C/U

- H: a receipt bound to session, canonical resource, generation, and source digest is reusable only while all bindings remain current.
- T: fresh Docker/Xvfb with two real GTK fixtures; bind receipt r1 to session s1, XID 2097155, generation 1, and source digest; test same binding plus restart, replacement, generation/source changes, cross-session, malformed, and duplicate cases.
- D: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :152, model/network calls 0.
- C: PASS_SESSION_RESOURCE_RECEIPT_BRIDGE_SCOPED. Only same-session/resource/generation/source admitted; every transplant, restart, replacement, stale, malformed, and duplicate case denied.
- U: receipt binding scope only. This does not establish model behavior, universal session identity, or broad GUI correctness. Effect transfer after receipt admission requires a separate application-boundary experiment.

The first attempt had a cross-session test-construction error; it was not used as the formal result. The corrected runner and result are retained here.
