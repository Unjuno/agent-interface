# Issue #2849 nested-runner response replay v27

Offline, no-task regression against the exact saved v26 Codex JSONL response. The additive nested runner preserves every event but counts only completed `agent_message` items, then hands the unchanged raw stream to the main selected backend, schema validator, and plain parser. One pinned outer and one pinned nested OrbStack container, both network-disabled. No host model or task fixture.
