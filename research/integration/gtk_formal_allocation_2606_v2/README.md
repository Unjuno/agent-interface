# GTK eight-case allocation after source-closure refresh

This is one fresh bounded local Docker allocation after the additive source
closure successor #2796. It preserves all earlier #2606/#2780/#2804 results.

Image: `agent-interface-gtk-formal-v3:2796`; network: `none`; cases: 8 in
fixed order; input operations: 3; model calls: 0; network calls: 0.

The runner reached all eight cases. Expected and actual scorer dispositions
matched, receipt order passed, and the independent gate classified useful,
unavailable, guarded, no-effect, partial, stale-repair, ambiguous-no-replay,
and cleanup-failure as preregistered. The runner scope remains explicitly a
receipt-emission preflight, not formal #2606 acceptance: the formal acceptance
claim remains open pending an independent audit of all raw effects/lifecycle
evidence.
