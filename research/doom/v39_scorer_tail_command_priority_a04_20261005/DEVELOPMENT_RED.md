# Initial failing regression on the current PR head

Before changing the implementation, this exact command was run:

```text
python -m pytest research/doom/test_map01_scorer_stdio_adapter_v1.py -k command_ready_during_callback_deadline_overrun_preempts_next_scorer_sample -q
```

It failed at the intended branch assertion: the callback advanced the clock
from 0 ns to 125 ns, past the 100 ns deadline, and made a complete command
readable, but the tail returned `deadline_overrun` rather than
`command_ready`. The method stopped before checking readability. This was a
local test-first diagnostic, not a candidate or formal allocation.
