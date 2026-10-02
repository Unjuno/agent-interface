# Corrected construction allocation, not replacement of live-01

One new allocation, seed 1001077, same task A1=317/A2=529 and no-input-retry rule.
Source 49c965df4 (full revision in built manifest). Prior live-01 remains
HOLD_SETUP_WINDOW_DISCOVERY with blank workbook and nonzero owner exit.

Only setup correction: use the already exported production read_window_title,
which reads UTF8 public titles before legacy WM_NAME; retain legacy and portable
values during window discovery. No input/decision/selection/STOP gate is loosened.
This may diagnose the title mismatch in this allocation; it cannot retroactively
prove why the earlier uninstrumented setup timed out. Maximum one new allocation.

All primary operation, independent scoring, no replay/automatic selection/sensor,
900s deadline, after-terminal oracle and cleanup requirements of live-01 PLAN
remain. Exercise same explicit packaged stdio persistent-x11 path. The primary
must view/review actual images, select modal explicitly with its one-use ID,
use returned binding revisions, inspect original releases, public close and EOF.

This is the next construction version of the existing integration gate, not
an extra scientific benchmark or a matched #57 comparison. Preserve any failure
without launching another version in this allocation. Generic efficiency HOLD;
actual token/billing measurements unavailable unless retained separately later.
