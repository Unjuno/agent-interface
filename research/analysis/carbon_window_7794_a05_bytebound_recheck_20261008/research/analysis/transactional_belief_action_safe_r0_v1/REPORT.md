# #1817 retained execution stop

Disposition: **FORMAL_EXECUTION_STOP_TIMEOUT**  
Scientific disposition: **NONE**

The first and only monolithic depth-8 formal invocation exceeded the 120-second external execution envelope. The process was terminated by the execution wrapper.

Post-stop checks:
- `RESULT.json`: absent;
- `AUDIT.json`: absent;
- surviving formal process: none;
- formal attempts: 1;
- reruns: 0.

The scientific hypothesis and state-machine semantics are not classified from construction evidence. Construction had already exposed and retained one excluded harness-depth gate mismatch; after a construction-only repair, construction passed. The exact formal source was frozen and read back from GitHub 3/3 before the monolithic formal attempt.

This allocation must not be rerun. A successor may preserve the exact depth-8 trace universe and semantics while changing only the execution envelope, for example by partitioning the eight top-level operation prefixes into immutable batches and aggregating exact integer counters.
