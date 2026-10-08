# Development calibration

Before source freeze, one private Xvfb/Openbox 60-trial matrix established discriminator behavior.

- unit model tests: 9/9 PASS;
- `content_only_prefix`: 30/30 predeclared negative/positive gates; exact only 5/30 fresh cases, 0 refusals;
- `bound_prefix`: 30/30 gates; 5/30 fresh cases exact, 25/30 metadata/identity/focus faults refused with zero recovery input;
- each bound rejection reason occurred exactly five times: stale_sequence, stale_binding, wrong_target, stale_age, focus_mismatch;
- stop=5 examples: stale sequence observed `bookk` while A had `book`; content-only appended `eeperoffice` -> `bookeeperoffice`, bound refused. Wrong-target observed B=`bookk` while A=`book`; content-only corrupted A similarly, bound refused. Focus-change sent the suffix into B under content-only while bound refused.
- X keymap unchanged; post-trial physical input empty.

This development run is not the retained formal result. No formal result ID was consumed. Formal schedule remains the fixed 60 trials in PLAN.md.
