# A08 result

A08 observed all input-owner recovery gates: the independent observer saw `a` down/up and keymap down/up, the session exited `-9`, the identity-matched fsynced receipt verified recovery, and the owner service exited `0` without forced termination. The supervisor sent Xvfb termination, but this Xvfb returned clean exit code `0` rather than the frozen required `-15`. Under A08's frozen rule, record `SCOPED_GATES_PASS_CONTROL_EXIT_CODE_MISMATCH`; do not relabel it as PASS. A09 may predeclare acceptance of clean controlled Xvfb exits `0` or `-15` and record the signal action.
