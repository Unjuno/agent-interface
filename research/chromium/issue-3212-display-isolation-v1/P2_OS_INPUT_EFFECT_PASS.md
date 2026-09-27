# #3266 p2 OS input to application effect — scoped PASS

Decision: PASS_P2_OS_INPUT_EFFECT_SCOPED

## H/T/D/C/U

- H: A currently displayed p2 Chromium window can receive one bounded OS key event after target selection and produce an independently observable application effect.
- T: Fresh Debian bookworm-slim container; Xvfb :221; Openbox; Chromium p2 with fresh profile/CDP 9331; install a keydown listener through the current page target; activate the discovered visible X11 window; send x with xdotool; read document.title through a separate CDP evaluation.
- D: Retain the CDP page websocket, exact input command, and exact post-input title. This is a single p2 input/effect probe, not a p1/p2 generation allocation.
- C: PASS requires the key event command to complete and the independent title readback to equal os-input-p2.
- U: No p1 stale-target control in this allocation, no cross-application reliability, no full identity/effect acceptance gate, no production integration.

## Obstac result

- page websocket: ws://127.0.0.1:9331/devtools/page/45018C46707C0BF94DDE49B9A218C69E
- input: xdotool windowactivate --sync followed by xdotool key --window <current-window> x
- readback: title=os-input-p2
- result: OBSTAC_P2_OS_INPUT_EFFECT PASS

The input listener was installed on the current p2 page target before the OS key event. The result proves only this bounded X11-to-page effect path on the pinned container fixture.

## Next gate

Combine this positive input/effect path with the already retained p1/p2 composite identity and stale-target negative control in one frozen allocation. Preserve all receipts and reject any target whose generation evidence is incomplete.
