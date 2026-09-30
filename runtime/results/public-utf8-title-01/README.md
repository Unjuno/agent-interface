# Public target inspection: UTF-8 title recovery

Primary Calc use in ../calc-compact-primary-01 showed an empty inspected main
window title despite a visible title bar. Public inspection only read WM_NAME;
the guarded route already considered UTF-8 title properties. Public inspection
now reads _NET_WM_NAME, then _NET_WM_VISIBLE_NAME, then the legacy property.
Empty UTF-8 titles fall through. Malformed UTF-8 or a non-8-bit typed property
refuses inspection, rather than fabricating a title. Titles remain untrusted
application metadata; no family, focus, selection or input guard is relaxed.

Fresh private real-X11 Calc read-only construction (seed 991352) reproduced:
baseline title empty; candidate title `sheet.xlsx — LibreOffice Calc`.
Independent xprop output showed WM_NAME encoded as COMPOUND_TEXT and that exact
_NET_WM_NAME value encoded as UTF8_STRING. The legacy get_wm_name() call returned
empty; the underlying WM_NAME property was not empty. The fix reads the supported
UTF-8 property rather than adding a COMPOUND_TEXT decoder.
All other target evidence was equal and backend input emissions remained zero.
The fixture setup launched/focused Calc; this is not a no-side-effect fixture.
No task input, saved-task evaluation or latency comparison was performed.

The first construction attempt failed before backend creation because the local
diagnostic passed its constructor arguments incorrectly. Its source, cleanup and
retrospectively recorded error are retained as public-title-calc-01. The corrected
diagnostic used a fresh allocation public-title-calc-02; no earlier output was
overwritten. Both fixture process sets were reaped. This setup correction did not
change the candidate implementation.

Local checks: 272 protocol +125 harness/distribution tests passed. Focused tests
cover legacy fallback, Unicode with empty legacy title, empty UTF-8 fallback,
invalid UTF-8/format refusal, unrelated client rejection and unmapped modal
refusal. Native source, tests, diagnostics, raw property output and logs are
retained with hashes. The manifest pins the implementation commit.

Run `python3 -O runtime/results/public-utf8-title-01/verify.py`. This read-only
verifier checks retained bytes and the concrete title/evidence/input result; it
does not execute archived source. This is a metadata usability repair, not
authentication, task correctness, speedup or real-time performance evidence.
