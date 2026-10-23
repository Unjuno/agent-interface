# R35 — sub-second low-level-hook delivery diagnostic

R34b observed Q-up during a 1250 ms post-cancel callback hold but recorded no second Q-up hook event. Microsoft documents a 1000 ms maximum configured LowLevelHooksTimeout on modern Windows and silent hook removal after callback timeout; R34b's actual callback lasted 1442 ms.

R35 is a separate diagnostic, not a relaxation or substitute for the frozen 1250 ms gate. It holds the first Q-up callback for 700 ms after cancel, starts a separate state-sampling process before dispatch, samples every 10 ms, and caps projected total callback time at 950 ms before it permits cancel. It checks for same-generation Q-up after the recovery SendInput return but before callback release, then records whether a distinct second Q-up callback arrives under the sub-second condition.

One fixture, one public dispatch, at most one cancel, no retries/replay. The fixture click/save still precedes cancel; task_success stays null. If the 950 ms projection fails, the probe releases the hook and stops before sending cancel. This diagnostic cannot pass the R29 strict 1250 ms gate.
