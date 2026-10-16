# Executor Child Hard-Kill with Resident InputOwner A02

**Formal status: STOP.** One candidate run SIGKILLed the Executor child, observed its RPC EOF, and returned from `InputOwner.close()`. It then raised `AttributeError` while attempting to inspect the owner through a nonexistent nested `_inner` attribute. Because the raw record has no owner-release record, post-close keymap sample, or independent KeyRelease, this run cannot establish recovery. Xvfb shut down cleanly. The run is not repeated; A03 is the corrected successor.

The surviving-owner hypothesis remains unresolved by A02. See the raw-only audit and `results/A01/RAW.json`.
