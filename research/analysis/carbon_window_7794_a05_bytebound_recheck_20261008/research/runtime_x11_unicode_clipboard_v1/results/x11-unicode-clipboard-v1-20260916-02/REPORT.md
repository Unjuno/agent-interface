# X11 Unicode clipboard lowering v1 — retained successor result

**Result ID:** `x11-unicode-clipboard-v1-20260916-02`  
**Source/plan freeze:** `f5e956b6824d33a45fb6c96abaadede7758eae05`  
**Prior formal result:** `x11-unicode-clipboard-v1-20260916-01` — retained harness failure, never rerun.

## Disposition

**PASS_SCOPED_UNICODE_CLIPBOARD_LOWERING / REQUIRE_EXPLICIT_SIDE_EFFECT_CAPABILITY / HOLD_GENERIC_TEXT_PROMOTION**.

The repaired invocation used the exact frozen execution-code blobs from the failed `-01` attempt; only the formal output-path contract changed to an absolute path. Writer then Calc each executed once on fresh private Xvfb/Openbox/LibreOffice sessions.

## Durable Unicode result

Both Writer ODT and Calc XLSX independently score exact for the fixed corpus:

`café`, `βeta`, `東京`, `あいうえお`, `🙂`, `e`+U+0301, `naïve`, `résumé`, `中文`, `한국`.

Writer output SHA-256: `90ca29416407d6d668db840bf05c3d9ae0d5e4e4a5a1205bcb8e54456256d8f9`.  
Calc output SHA-256: `03f8e28c6a183b80fed270b539cf2ad4574f5c0257bd122b7c4253d09339cec1`.

Both executor and independent scorer exit 0. Both artifacts pass ZIP CRC readback.

## Freshness / release / state gates

For **both** apps:

- stale observation is refused as `STALE_OBSERVATION` before clipboard/input mutation;
- stale CLIPBOARD owner ID is unchanged;
- stale CLIPBOARD UTF-8 text remains exactly `PREVIOUS-αβ`;
- after fresh paste, the previous UTF-8 text is restored exactly while the candidate lease remains alive;
- X keyboard mapping is unchanged;
- terminal physical input is empty (`keys=[]`, `buttons=[]`).

## The side effect that blocks generic `input.text`

Prior CLIPBOARD owner ID is `4194307`. During the candidate lease it becomes `12582915`. After restoring the **text bytes**, owner identity remains `12582915`; after lease close it still does not return to the previous owner. The old owner process was intentionally kept alive.

Therefore restoring clipboard text is **not** transparent clipboard restoration. The mechanism also does not prove preservation of TARGETS/rich MIME/clipboard-manager semantics. It must not silently advertise generic `input.text` semantics. A future interface needs an explicit side-effect contract/capability if this lowering is exposed.

## Retained candidate rejections

Before source freeze:

- Ctrl+Shift+U composition produced literal `u...` strings in Writer and was rejected;
- Unicode KeySym remapping could deliver text but altered global X keymap structure (`keysyms_per_keycode` expanded) and was rejected for default use;
- clipboard lowering was selected only after these failure modes were retained.

## Formal harness failure retained

The first source-frozen `-01` result stopped before any input because a relative `--out` leaked into LibreOffice `file://` profile URI construction. That result is retained at commit `f8b0aebc22a99d4d98b96146d940bd40ab77e340` and was not rerun. The successor changed only the invocation contract to use an absolute output path; execution-source blobs remained unchanged.

## H/T/D/C/U

**H:** UTF-8 clipboard paste can close bounded Unicode durable semantics on X11, but clipboard ownership makes it a side-effecting mechanism rather than transparent generic text.  
**T:** source-frozen Writer→Calc real-Office matrix, separate durable scorers, stale/clipboard/keymap/release controls, zero model/provider/network calls.  
**D:** scoped Unicode PASS because both apps and all hard controls pass; generic text promotion HOLD because owner identity is not restored.  
**C:** rich MIME/TARGETS, clipboard managers, app dialogs, selection ownership and locale may differ; Calc needs Text Import confirmation.  
**U:** private Xvfb/Openbox only; clipboard UTF-8 lowering is not full IME composition and says nothing about Wayland/Windows/macOS/WSLg.

## Successor

Do **not** hide this behind generic `input.text`. The next useful design experiment is a first-class text-delivery capability model that distinguishes direct key synthesis, clipboard-mutating paste, accessibility value-setting and native IME routes, with declared side effects and fallback ordering. Platform implementations should then prove the strongest non-destructive route available on each OS.
