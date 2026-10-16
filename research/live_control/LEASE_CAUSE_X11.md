# Actual X11 interruption cause propagation

One scripted private-Xvfb experiment exercised input_owner_v10 and executor_v4
together. Control_L was physically down according to XQueryKeymap before transferring
focus to a private sink window. The independent owner released it; XQueryKeymap
confirmed it was up. Focus was returned, then another down request using the old
lease correctly raised DecisionRequired. The terminal carried the original verified
focus_changed release under that lease's unique token, alongside the separate final
cleanup release. This terminal arrived before owner/session shutdown.

A fresh second intent used exactly the same deadline, held the key, completed and
released it. Its terminal had no inherited interruption. This exercises identity
isolation through actual owner and executor code, beyond the prior synthetic probe.
Executor, owner and session close calls returned. The fixture does not provide a
structured independent per-process cleanup inventory.

Evidence: `results/lease-cause-x11-01/report.json`; source hashes, all executor events,
owner records and checks are retained. `probe_lease_cause_x11_v1.py` uses an exclusive
result directory; keep the measured run and use a new allocation for further runs.

Scope: one controlled keyboard focus transfer, not pointer geometry/cancellation/
expiry coverage, a full app task, autonomous model use, or a speed comparison. The
probe intentionally uses a small backend to isolate owner/executor behavior. It does
not switch existing app fixtures. Guards without an active release can still have
no structured cause; null must remain unknown. The first owner interruption is
evidence of a stop condition, not a complete physical root-cause explanation.

Next connect the candidate pair through an explicitly versioned app fixture and
compact-index path; verify the additive terminal fields survive transport and remain
visible on an actual interrupted task. Keep the older default runtime and all frozen
comparisons unchanged. Do not infer task recovery improvement from this foundation
test alone.
