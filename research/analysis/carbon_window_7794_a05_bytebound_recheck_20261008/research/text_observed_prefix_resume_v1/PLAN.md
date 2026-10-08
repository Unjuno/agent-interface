# Text observed-prefix resume v1

H: after mid-flight interruption, application-reflected text is a safer recovery boundary than sender-side `chars_sent`; resume only when the independently observed current text is an exact prefix of intent.

T: private authenticated Xvfb/Openbox plus separate Tk consumer. Desired text `bookkeeperoffice`; stops 3/5/8/12/15; faults clean/tail-swallow/middle-swallow/external-mutation; policies blind-full/sender-count-suffix/observed-prefix-suffix = 60 fixed trials. Candidate refuses non-prefix state with zero recovery input. Independent receiver IPC supplies reflected text only for this research fixture.

D: every predeclared gate must match: observed-prefix exact on clean and tail-swallow; observed-prefix zero-input refusal on middle-swallow/external-mutation; sender-count exact only on clean and wrong on the other faults; blind-full wrong for all nonempty stops. Physical input empty and keymap unchanged. Refusal is safety, not task completion.

C/U: fixture readback is not a product observation mechanism; real applications may expose stale/ambiguous text. No atomic rollback, Office/Unicode/IME/3OS/model/token claim.
