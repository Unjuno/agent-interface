# Construction history — Issue #27 MotorState first rung

Construction is excluded from the 18-case formal denominator. Earlier failures are preserved rather than rewritten:

- initial construction: `XVFB_NOT_READY` from Xauthority/setup; no scientific row;
- subsequent setup: app focus/lifecycle and outer 45 s timeout; `STOP_CONSTRUCTION_TIMEOUT_AND_FOCUS_SETUP`; formal=0;
- final setup-only repairs: pass private Xauthority to Python-Xlib, use normal-click/current-focus identity, match LibreOffice Calc by WM_CLASS, fresh per-case LibreOffice profile, and bounded process-group cleanup;
- GitHub-readback source smoke: Inkscape 3/3 and Calc 3/3 pass before formal.

These fixes were completed before the public source freeze and do not alter the frozen scientific comparison.

Selected retained local construction RAW identities:
- construction-00 SHA256 `75606f534506e949658754887d0db863e36921a710fbacb16dfcad7b3282520c` — six setup errors;
- construction-v2-ink5 SHA256 `75efc41e1fdd1aaa9ecfbd3a7aa964896a710d647ab046520b0d8e9e1a5c4479` — 3/3 ok;
- construction-v2-calc3 SHA256 `8d118732fb52e83884c80e51379ca470260e06d7043e8bf6600394cd81b27225` — 3/3 ok;
- GitHub-readback smoke Inkscape SHA256 `93cfc19a727d0862fa12e9495017d11cede107a571e84bfbfab5362c497cdf24` — 3/3 ok;
- GitHub-readback smoke Calc SHA256 `a2de4b86a025390edc9ba829b7f2388555c76954d270d2d94d54c957f0f094cb` — 3/3 ok.

The complete local construction history remains outside the formal denominator; no failed construction row was relabeled as science.
