# Development calibration

One private Xvfb/Openbox 60-trial development matrix completed before source freeze.

Observed qualitative discriminator:
- blind full retry: 0/20 exact, all negative-policy expectations matched;
- sender-count suffix: exact only in 5/20 clean-stop cases; tail swallow produced `bookeeperoffice` at stop 5 despite `sent_count=5`;
- observed-prefix: exact in all 10 recoverable clean/tail-prefix cases and zero-input refused all 10 non-prefix middle-swallow/external-mutation cases;
- keymap unchanged; final physical input empty.

This calibration is not the retained formal result. Formal schedule remains the fixed 60-trial matrix from PLAN.md.
