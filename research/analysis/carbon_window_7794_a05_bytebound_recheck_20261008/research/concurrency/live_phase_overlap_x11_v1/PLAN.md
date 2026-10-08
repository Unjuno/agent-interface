# Live phase-overlap X11 formal — #1688

Parents: #1670 and #23.

## H
With one serialized X11 keyboard actuator and two independent surfaces, input B may be admitted while A's 150 ms effect tail is pending, preserving exact A/B visible effects while reducing action-start to both-effects wall time. A deliberately hidden shared root-property dependency must contaminate A under unsafe overlap and remain correct under serial execution.

## T
Fresh private Xvfb per case; raw Xlib fixture windows; XTEST core keyboard; independent pixel scoring from the X server. Four frozen arms x six first outcomes = 24 cases: serial_independent, overlap_independent, serial_shared, overlap_shared. Fixed schedule in schedule.json. One formal invocation, no retries/replacements/tuning.

## D
PASS_LIVE_PHASE_OVERLAP_X11_SCOPED iff:
- serial_independent 6/6 exact A=red/B=blue;
- overlap_independent 6/6 exact A=red/B=blue;
- serial_shared 6/6 exact A=red/B=blue;
- overlap_shared 6/6 exact preregistered contamination A=B/B=B with pixel scorer rejecting A;
- exactly one KeyPress per surface and terminal Space key neutral in all 24;
- overlap arms have B KeyPress before A effect, serial arms A effect before B KeyPress;
- median overlap_independent wall <= 0.65 * serial_independent median and reduction >=100 ms;
- source/schedule/audit integrity passes.

## C
Real apps may retain focus/input resources during effect-pending time, tails may share clipboard/window-manager/modal/global state, or B may semantically depend on A. Those cases invalidate overlap eligibility.

## U
Synthetic Linux/Xvfb/XTEST two-surface fixture only. The 150 ms tail is intentionally controlled. No real-app/model/token/human-tempo claim.
