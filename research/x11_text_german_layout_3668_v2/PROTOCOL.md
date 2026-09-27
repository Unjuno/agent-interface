# Issue #3741 preregistration

## H / T / D / C / U

### H — hypothesis
The current-main X11 text planner resolves "=" and "*" on standard German XKB and private-Xvfb XTEST events decode to the exact formula. Late unsupported text refuses before any event. Server support is tested by the server extension list; Python-Xlib has_extension("XKEYBOARD") is recorded separately because the v1 probe showed it can be false while the server advertises XKEYBOARD.

### T — frozen target
- Allocation: issue3668-german-xkb-text-v2.
- Main source base: f79ef46d478911170d73b71bddcbe58fd698dc84.
- Runtime source: runtime/backends/x11_v1/backend.py; Git blob 9cae101a219348077668c8fc086acf8e13154afe.
- Frozen probe Git blob: 5124909952510da278658c5a45decf314786ab36.
- Frozen auditor Git blob: 0c100e80122780341b0e0cc98aa1b81f6088feb9.
- WSL environment: Ubuntu 24.04.4; Python 3.12.3; Xvfb 2:21.1.12-1ubuntu1.6; x11-xkb-utils 7.7+8build2 (setxkbmap 1.3.4); xkb-data 2.41-2ubuntu1.1; xkbcomp 1.4.6; xmodmap 1.0.11; python-xlib 0.33.
- Four fresh Xvfb servers, fixed order: de-01, de-02, de-03, us-control. Each 1024x768x24. Require baseline layout US. Three German rows each apply exactly setxkbmap -layout de once; US control changes nothing.
- Gate server XKEYBOARD/XTEST using Display.list_extensions(); log has_extension() values without treating a missing client-side XKB binding as server absence.
- Each run records complete before/after server XKB, core and modifier maps; layout; source identity; symbol levels; chords; refusal; actual XTEST KeyPress decoding; emission counts; release state.
- Before valid input, preflight =B2*A2€ and assert refusal with zero emissions and receiver events. Then emit =B2*A2 once into a private receiver and drain a short quiet interval for extra characters.
- PASS gates: all four exact formula decodes; both symbols resolve at level 0/1 and match planned chords; German maps change from US baseline; US map remains stable; zero-input refusal; no held keys; independent audit PASS.
- Commands: per row use a fresh Xvfb, with the probe arguments from PROTOCOL. No loop-level retry. The only difference across the four commands is the frozen layout/replicate/output argument.

### D — decision
PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED only if every frozen row and gate passes. Wrong/missing/extra characters or any event before unsupported refusal is FAIL. Missing server extension, tool, or source identity is STOP/HOLD. No retry or gate/source adjustment under this allocation.

### C — constraints
Docker Desktop is unavailable (Windows service Stopped/Manual; WSL client has no responding daemon). Clearly labeled WSL host-Xvfb fallback only; no container evidence. Private Xvfb only: no host display, physical keyboard, GUI application, Calc, MCP/model, network, package installation, user data or production source change. Preserve every failure and cleanup row.

### U — limits
German two-level XKB and this X11 backend only. No Calc task effect, public API/MCP, actual German keyboard, level3/Compose/dead-key/IME, non-X11, performance or broad layout claim.

## Preserved predecessor STOP
#3733 remains immutable. Its first row stopped before layout or input because the runner used Python-Xlib has_extension("XKEYBOARD"). A separate diagnostic found server list_extensions() contained XKEYBOARD and XTEST; the corrected gate in this successor addresses only that harness prerequisite. No hypothesis observation was made in v1.
