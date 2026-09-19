# Crash-loss-point preflight for native exchange #2704

This additive preflight exercises the durable request/reply state machine with
an isolated local owner process at each registered loss point. It is not the
formal native Calc allocation: the owner uses a disposable event/effect file,
so the result cannot establish native input emission or GUI effect correctness.

The formal allocation remains gated on replacing this disposable owner with the
private X11/Calc owner and an independent input/effect/release audit.
