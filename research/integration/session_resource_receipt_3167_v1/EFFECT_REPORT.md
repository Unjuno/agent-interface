# Session/resource receipt effect transfer

Issue: #3167.

This successor experiment closes the prior report's stated effect-transfer gap.

- Docker: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :153.
- Two real GTK/X11 fixtures: receipt resource XID 2097155 and replacement XID 4194307.
- Valid receipt: admitted, 4 physical emissions, runtime completed, independent effect receipt present.
- Replacement, cross-session, and duplicate receipts: denied before dispatch, 0 emissions, no effect.

Decision: PASS_SESSION_RESOURCE_EFFECT_TRANSFER_SCOPED.

Scope remains one GTK/X11 topology and declared receipt binding. No broad GUI, model, or production claim follows.
