# #1282 P0 live-transfer closure

H/T/D/C/U are frozen in Issue #1282.

Source facts are deliberately minimal: merged #1100 current DAG closure plus merged #1276 live physical-edge transfer. The audit may promote only LIVE_PHYSICAL_EDGE_TRANSFER from UNPROVEN_CURRENT to PROVEN_LIVE_SCOPED. It must leave LIVE_CAUSAL_EFFECT_SAMPLE unproven and live useful-control false.

One deterministic invocation; reruns/tuning0. No X11, model, provider, network or task input.
