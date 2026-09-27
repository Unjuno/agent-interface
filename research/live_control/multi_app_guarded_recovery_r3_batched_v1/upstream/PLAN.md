# R3 repeated mixed-app guarded recovery

Task: `MULTI-APP-GUARDED-RECOVERY-R3-20260918-003`, Issue #1769.

H: the exact #1728 fail-closed/refreshed-recovery semantics remain correct when the four-transition cycle is repeated three times in one live Chromium+XTerm session.

T: same private Xvfb/Openbox, Chromium, persistent XTerm, Python-Xlib/XTEST, built-in Downloads/History effects, direct-WM recovery, and four fresh formal sessions as #1728. Change only repetition count from 1 to 3 cycles/session. Each cycle uses a fresh replacement Chromium profile/window. Construction excluded. Formal once; reruns/replacements/tuning0.

D: every formal session must complete 3 cycles, 12 ordered refusals with no task-input increase, 12 active-target-matched fallback batches, exact Downloads/History/Downloads/History effect sequence repeated 3x, 3 valid adjacent replacements, and terminal neutral. Aggregate gates: 48/48 refusal zero-input, 48/48 active target/effect, 12/12 replacement validity, terminal4/4. Integrity/audit pass.

C: repeated fresh process/profile creation may expose lifecycle/resource behavior rather than guard semantics. Construction descriptively observed X11 raw window-ID reuse across non-consecutive generations; this is not a posthoc R3 decision gate and does not prove identity safety.

U: finite 3-cycle Linux private-X11 result only; no endurance/model/token/latency/human-tempo/cross-backend claim.
