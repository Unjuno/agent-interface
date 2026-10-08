# Issue #8406 T0 A01 — schedule-harness contract

This no-model probe reuses the exact immutable 12-episode fixture from merged Issue #7418 T0. It changes only when an exact, lossless derived manifest is checkpointed: episodic-only, after every episode, every four episodes, or once at terminal prefix 12. At fixed prefixes 3/6/9/12, a deterministic evidence lookup reports which source IDs are available to four held-out query classes. It emits no answer, skill, action, or authority.

The result can validate schedule construction, provenance, checkpoint alignment, and audit controls only. It cannot demonstrate schedule-induced LLM memory degradation or GUI task behavior. See [`PROTOCOL.md`](PROTOCOL.md) and `FREEZE.json` for the frozen H/T/D/C/U, source fixture, and commands.
