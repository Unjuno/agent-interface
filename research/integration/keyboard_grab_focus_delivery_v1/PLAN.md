# Issue #4159 — keyboard-grab focus-delivery boundary

Allocation: `keyboard-grab-focus-delivery-20260923-01`.

H/T/D/C/U are registered prospectively in Issue #4159. The excluded construction corrected one pre-formal wording: A is observed focused **before** the directed foreign grab; an active XGrabKeyboard may itself make Tk focus reporting temporarily unavailable. The formal factor is therefore the focus-check-to-key delivery interval, with an optional grab probe after the focus basis.

Formal schedule: 2 policies × 3 states × 3 repetitions + 2 NO_TASK_INPUT controls = 20 fresh cases. One supervisor invocation, no retry/replacement/exclusion/tuning. Private authenticated Xvfb `:96`; exact sources and hashes in FREEZE.json. Scientific outcomes use actual application/grabber journals and X-server cleanup, not process success alone.
