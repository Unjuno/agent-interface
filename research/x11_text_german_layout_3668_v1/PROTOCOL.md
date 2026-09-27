# Issue #3733 preregistration

## H / T / D / C / U

### H — hypothesis
On the standard German XKB layout, the current-main X11 text planner resolves "=" and "*" from the active keymap and actual isolated XTEST key events decode to the intended ASCII formula. A late unsupported character remains fail-closed before any event.

### T — frozen target
- Allocation: issue3668-german-xkb-text-v1.
- Main source base: f79ef46d478911170d73b71bddcbe58fd698dc84.
- Runtime source: runtime/backends/x11_v1/backend.py, Git blob 9cae101a219348077668c8fc086acf8e13154afe.
- Frozen probe: run_probe.py, Git blob 714551e990ce972ee8e14aad635b99256b91d0eb.
- Frozen independent auditor: audit.py, Git blob e2a0a3f4bd8bd413673d9fe6655d426313524115.
- Environment preregistration: Ubuntu 24.04.4 WSL; Python 3.12.3; Xvfb 2:21.1.12-1ubuntu1.6; x11-xkb-utils 7.7+8build2 (setxkbmap 1.3.4); xkb-data 2.41-2ubuntu1.1; xkbcomp 1.4.6; xmodmap 1.0.11; python-xlib 0.33.
- Four fresh Xvfb processes in fixed order: de-01, de-02, de-03, us-control. Each uses a new Xvfb server at 1024x768x24. Before each run, verify the server baseline layout is US. For each German row, the probe applies exactly setxkbmap -layout de once. The US control applies no layout command.
- Each probe records the complete before/after server XKB, core keymap, and modifier-map text, active layout query, exact source blob/hash, symbol levels, planned chords, refusal control, actual XTEST KeyPress decode, emissions, held-key state, and cleanup.
- The unsupported control is preflight-only: =B2*A2€ must be refused with zero emissions and zero receiver events. Then and only then the probe emits =B2*A2 exactly once into a private receiver window and records all keypresses through a short quiet drain.
- Required checks: every German row and the US control decode exactly =B2*A2; symbol chords agree with active level 0/1; all three German server/core/modifier maps change from the US baseline; the US control maps remain unchanged; release state is empty; and the independent auditor accepts every required row.
- Run command per row from the repository root (fresh server each time):
  xvfb-run -a -s "-screen 0 1024x768x24" python3 research/x11_text_german_layout_3668_v1/run_probe.py --layout de --replicate de-01 --output research/x11_text_german_layout_3668_v1/results/de-01.json
  Repeat only the frozen replicate label/output for de-02 and de-03; then run once with --layout us --replicate us-control --output .../us-control.json.
- Audit command:
  python3 research/x11_text_german_layout_3668_v1/audit.py research/x11_text_german_layout_3668_v1/results --output research/x11_text_german_layout_3668_v1/results/AUDIT.json

### D — decision
PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED requires all four exact decoded strings, correct keymap/chord agreement, all fail-closed/release conditions, map-transition controls, exact frozen source identity, and independent audit PASS. Wrong, missing, or extra characters or any event emitted before unsupported refusal is FAIL. Source/tool/setup integrity defects are STOP/HOLD, not hypothesis results. No retries, layout substitutions, or changes to gates under this allocation.

### C — constraints
The Windows Docker Desktop service is Stopped/Manual and the engine has not responded; the WSL Docker client also has no responding daemon. This preregisters a clearly labeled WSL host-Xvfb fallback, not container evidence. No host display, physical keyboard, Calc/application, model, MCP, network, package installation, user data, or production source change. XTEST events are confined to a disposable private Xvfb receiver. Preserve every run and any failure.

### U — limits
Standard German two-level XKB and this exact X11 backend only. No Calc task effect, public API/MCP, real German keyboard, level3/Compose/dead keys/IME, non-X11 backend, speed/cost benefit, broad keyboard-layout, or product claim.

## Provenance
This work is a successor to closed #3668/#3670. Preserve all predecessor evidence unchanged. #412/#418 established German XKB server-state changes but intentionally sent no key events; this allocation tests runtime symbol selection and isolated event decoding, not that prior server-state prerequisite.
