# #2699 v3 launch-provenance result

Date: 2026-09-20

Decision: `FAIL_XAUTH_COOKIE_IDENTITY`

The additive v3 image preserves v2 and uses supported Inkscape arguments plus
an isolated LibreOffice profile. The strict resolver requires exactly one
validated candidate per application.

- Inkscape: 2 candidates (main window plus auxiliary `org.inkscape.Inkscape`)
- Calc: 2 candidates (main Calc plus `Tip of the Day`)
- Chromium: 1 candidate (`about:blank - Chromium`)
- missing-token control: 0 and refused
- input/model/network: `0/0/0`

All three applications started, so this is an ambiguity failure rather than a
startup stop. The strict refusal is retained. The next resolver successor must
preregister deterministic auxiliary-window filtering and main-surface binding;
it must not silently choose one candidate from this run.
