# TEXT-PAYLOAD-XKB-DISPOSABLE-V2

This is a separately allocated successor to retained formal failure `text-payload-xkb-layout-v1-20260916-01`. The failed result is not rerun or pooled.

The v1 hard gate proved that fixture `XChangeKeyboardMapping` projection is not byte-exactly reversible inside this Xvfb/XKB server: a saved 7-wide core map normalized to 15-wide on restoration. V2 therefore changes the **fixture isolation boundary**, not the candidate: each arm receives a fresh authenticated Xvfb process; standard XKB Group1 levels 0/1 are projected before candidate delivery; the candidate must leave that applied map unchanged throughout all 95 trials; the entire X server is destroyed when `xvfb-run` exits. No in-server restoration is claimed.

Fixed order: `us`, `de`, `fr`, `us(dvorak)`. Payloads are U+0020..U+007E, one character per trial.

PASS requires, for every arm:
- exact dependency blob `35c7375e50f3e0c58f57c8139a6dc8abeef87771`;
- non-US projection changes the fresh server core map;
- every candidate-accepted character is exact in the separate Tk consumer;
- every candidate-rejected character emits zero input and leaves consumer text empty;
- applied map fingerprint remains unchanged throughout delivery;
- physical input is empty after every trial;
- arm exits 0 under its private `xvfb-run` process boundary.

Coverage count is descriptive, not a score. Rejection is safe refusal, not delivery success.

Limits: Group1 level-0/1 core-map projection only. Fixture map projection itself is global within the disposable X server and is not a product text route. No full XKB types/AltGr/compose, Unicode/IME, Office, Wayland, Windows/macOS, token, or product reliability claim.
