# LibreOffice Calc X11 semantic integration v0 — retained first result

**Result ID:** `office-x11-calc-20260915-01`  
**Source/plan freeze:** `cd5e6593d094a392324e7534c83de535eab60469`  
**X11 backend dependency:** `c96fe562233be3ddeb5bb15018afef4cbd7fb755`  
**Portable contract dependency:** `0f2bda3c7d9eb863714795789dcfa2ea9fe86bd5`

## Disposition

**PASS_REAL_CALC_SEMANTIC_EFFECT / HOLD_GENERAL_OFFICE_PROMOTION**.

The source-frozen private Xvfb/Openbox/LibreOffice Calc first outcome passed transport, release and independent XLSX semantic scoring. It is one bounded spreadsheet task, not broad office reliability, native-platform support, or a model/token result.

## Retained outcome

- static construction tests: exit 0;
- runner / executor / independent scorer: exit 0;
- stale observation was refused as `STALE_OBSERVATION` with backend emissions `0 -> 0`;
- accepted task emitted **43** backend events;
- terminal release was verified with `keys_down=[]`, `buttons_down=[]`;
- input XLSX SHA-256 `f3262ecac99e45f0e7b19fd2c81898edab9e27f74f32a004720dc45ce6ad9807`;
- output XLSX SHA-256 `08eff6b2c8b938b15586952d5e27e0a038eb3270a463dbd14c4e4f97bfbcd03a` (6012 bytes), so the saved artifact changed;
- independent post-execution scorer recovered exactly `A1=office`, `A2=preview`, `A3=None`;
- OOXML archive readback verified 11 ZIP members without CRC error.

The executor/backend do not import the XLSX scorer or openpyxl and do not read workbook contents while acting. Workbook scoring occurs in a separate process after executor completion.

## Construction failures before source freeze

These were development calibration, not overwritten formal outcomes:

1. LibreOffice launch used invalid `--env:UserInstallation`; corrected to `-env:UserInstallation`.
2. The orchestrator initially omitted its own private `XAUTHORITY`, so Xlib window discovery failed before input.
3. Direct X11 `set_input_focus` and EWMH activation alone could emit/release input while leaving the XLSX unchanged: backend success did not imply application semantic effect.
4. Screen evidence then showed the Calc UI received `A1=ofice`, `A2=preview`: unpaced repeated `ff` lost one character, and the XLSX format-confirmation dialog prevented durable save.
5. The frozen candidate keeps the semantic AST unchanged but adds **12 ms strict-ASCII text pacing** as backend policy, EWMH activation via Xlib (no external `wmctrl` dependency), and a fixture/task-specific bounded confirmation Enter. The construction run then independently recovered the exact XLSX values before source freeze.

These failures show why target acquisition, delivery pacing, application confirmation and semantic scoring cannot be collapsed into one generic "input succeeded" flag.

## Wrapper anomaly

After the retained child run and audit summary completed, the outer container command display returned status 1 with `TERM environment variable not set`. The result ID was **not rerun**. The retained internal receipts remain: unit=0, runner=0, executor=0, scorer=0, `report.passed=true`, exact cells pass, and source blobs match the freeze.

## H/T/D/C/U

**H:** portable admission + a real X11 backend can produce a bounded durable office-file effect when office-specific delivery/focus policy is explicit.  
**T:** one source-frozen private Xvfb/Openbox/LibreOffice Calc XLSX task, one stale zero-input control, separate post-execution XLSX scorer; no model/provider/network.  
**D:** PASS for this scoped Calc task; HOLD for broad office or platform promotion.  
**C:** other office apps, dialogs, locales, IMEs, cell targets, WMs and real desktop compositors may require different acquisition/pacing/confirmation policies.  
**U:** one task/session, fixture-bound sheet coordinate, strict ASCII, Xvfb/Openbox only, uncontrolled timing, no WSLg/Wayland/Windows/macOS/model/token evidence.

## Successor

Do not promote a universal office method from this run. A useful next integration block should vary at least target cell/location and durable operation (e.g. formula/edit/save) under an independent workbook scorer, while retaining fresh target binding and release gates. Separately test Wayland/native backends rather than inferring them from X11.
