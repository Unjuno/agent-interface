# Successor #2110 — resident-reactive stale-event separation

Status: PASS_RESIDENT_REACTIVE_STALE_EVENT_SEPARATION_SCOPED

The stale control-plane message is rejected as an independent event and never removes or mutates an observation sample. Across 16 Boolean traces × 4 timings, all 64 stored rows match the independent rising-edge oracle, reject one stale message, and terminate with release.

This is a finite synthetic mechanism result only. Formal container execution is HOLD_DOCKER_UNAVAILABLE; no model, GUI, runtime, network, latency, token, production-safety, or transfer claim is made.

Reproduction: run python experiment.py, then python audit.py.
