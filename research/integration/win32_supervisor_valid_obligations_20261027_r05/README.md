# R05: stopped before supervisor exchange

The first R05 probe was intended to build a valid large Unicode obligation set and test the current Win32 supervisor against a blocked real pipe. The worker failed before constructing the request: its dynamic import did not register the contract module in `sys.modules`, causing the dataclass decorator to raise `AttributeError`. A peer had already started. The owning watchdog hit its six-second deadline and terminated the assigned job; the worker exited nonzero and a subsequent process inventory found neither worker nor peer.

This outcome does not measure supervisor send, release, task effect, or recovery. The source, stage traces, stderr, exit result and hashes are preserved unchanged. No GUI, game, model, native input, WSLc or Docker was used. A repaired probe must use a separate fresh output directory; this result remains STOP.
