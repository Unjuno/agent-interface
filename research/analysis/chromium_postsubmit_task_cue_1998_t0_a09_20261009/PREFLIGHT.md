# Pre-allocation full-frame OCR pilot

Before A09 registration, the retained Chromium epoch-8 full-frame PNG was passed once to Tesseract 5.5.2, English, PSM 11. The byte-exact stdout, stderr, exit, command, and input hash are retained in `preflight/`. Exit was 0, but stdout did not contain exact `t001101`; it included OCR text `Value [1001]`. This is construction feasibility context only, not formal evidence. The formal candidate will not rerun the full frame or this pilot and will process only the 20 fixed A04 crops.
