# #2699 v4 filtered identity result

Date: 2026-09-20

Decision: `PASS_XAUTH_COOKIE_IDENTITY_FILTERED`

Local Docker runtime used `mixed-app-2499-xauth:v4`, `--network none`,
read-only source, and tmpfs. The v4 resolver used preregistered role filters:

- Inkscape: exact `WM_NAME(STRING)` prefix `Inkscape `
- Calc: `WM_NAME` containing `LibreOffice Calc`
- Chromium: `WM_CLASS` containing `Chromium`

All three applications yielded exactly one selected main surface. Auxiliary
windows were retained but not selected: Inkscape's auxiliary class-title
window, Calc's `Tip of the Day`, and Xvfb/root windows. The missing-token
control remained refused. Input/model/network counters were `0/0/0`.

This is an identity-resolver gate only. It does not claim input, transitions,
effects, stale capability safety, or formal #2499 acceptance. The filters and
all candidate properties are retained in the runner output for independent
audit; no ambiguous candidate was silently promoted.
