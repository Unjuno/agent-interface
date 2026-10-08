# Generation-bound early evidence preparation (#2047)

## Disposition

**HOLD_PRE_LIVE_X11_MODEL**

The deterministic generation-bound harness ran once locally. It produced `ENCODED`, `OBSOLETE`, `CACHE_HIT`, and `ENCODED` for generation sequence 1, invalidated 2, reused 1, then 3. Obsolete evidence has no bytes and cannot be accepted; exact-generation reuse returns identical bytes. The intentionally stale unchecked control is detected and rejected.

Digest: `9d4e4bb50d9ed35bfba829f17a3b34fd6790c4152f2c0e74a07af8aeb5f317b4`.

## Boundary

Docker formal execution was stopped before invocation because the shared daemon had concurrent MAP01/import workloads; no competing process was interrupted. The local harness uses deterministic PPM bytes, not PNG, and has no X11, model, task input, packaging/provider, or end-to-end latency. It therefore does not establish model-facing value or live capture correctness. The next rung must bind generation IDs to an actual private-X11 capture and measure request-to-decision behavior.
