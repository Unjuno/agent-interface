# Win32 live fixture deferred native queue records r09

Date: 2026-11-10. Source main: `85849d1f0384f58e55a0c34abacae5797e002a31`. Route: public supervised Win32 MCP, one A chord, 2 s completion horizon.

After a matched public observation, the fixture continued dispatching non-keyboard messages but explicitly removed keyboard messages from its queue into a fixture-side list. The real queue yielded WM_KEYDOWN A and two WM_KEYUP A records. The action completed with a verified release receipt and 2 s/76-sample neutral horizon (maximum 32 ms gap). Only after the probe observed the terminal result did it unblock the fixture; those stored messages were reconstructed and dispatched at 77,401,687,000,000 ns, about 94 ms after the horizon ended (77,401,593,000,000 ns). No WM_CHAR event or application-visible task effect followed. Session and fixture were closed.

Classification: scoped post-horizon dispatch with no task effect. The fixture intercepted and manually reconstructed messages; it is not evidence of spontaneous stale Windows delivery, GZDoom/MAP01, broad reliability, or efficiency. `timeline.json` contains the same-session polling sequence; raw MCP reports and `events.jsonl` retain the primary evidence. Do not replay.
