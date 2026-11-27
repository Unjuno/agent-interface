# A04 result

A04 is preserved as `STOP_HARNESS_OBSERVATION_FAILURE`. The candidate started Xvfb and a session child, but the supervisor hit a JSON decode error on the child stdout channel before observing owner readiness or the held-key arm. The child termination closed the owner RPC channel; the recovery receipt was fsynced but reports `recovery_verified: false`, with X11 connection resets because Xvfb was already shutting down. This run is neither a pass nor a fail on the process-death hypothesis.

The candidate was invoked once. It will not be retried. A05 changes the observation channel to an append-only event file and is a new frozen allocation.

RAW SHA-256: `79fa4a37fefa932dcca84ef0266ab4c8f15bbd41006030fb67ab379db16462b7`
Receipt SHA-256: `d10880f96cb989813f6d3cc158318ca910fc1d45fd7f817e468759088f09e22a`
