# Win32 live fixture fully blocked message pump recovery r08

Date: 2026-11-10. Source main: `85849d1f0384f58e55a0c34abacae5797e002a31`. Route: public supervised Win32 MCP, one requested A chord, 2 s recovery horizon.

The fixture WndProc stopped pumping entirely after observation. Public dispatch returned pending, but the producer could not pass its start gate while the target UI was blocked; no input dispatch or fixture key event was observed. The probe made one bounded cancel request. Recovery eventually returned `recovered`, `release_confirmed=true`, `task_success=null`, `replay_allowed=false`, `input_dispatched=null`, and lower bound zero program actions; its recovery receipt records a 2 s/77-sample horizon with maximum 32 ms gap. The GUI pump remained blocked for 23.359 s and resumed after the probe's explicit unblock request. The fixture was closed and exited.

Classification: useful bounded recovery after a scheduling/method failure; it does not test stale queued input or post-horizon task effect because the action never began. It is not a task-effect pass, GZDoom/MAP01, general reliability, or efficiency evidence. Preserve the pending/cancel/recovery sequence in `timeline.json` and the durable producer/raw MCP records; no replay.
