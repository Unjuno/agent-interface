# TEXT-PAYLOAD-XKB-LAYOUT-TRANSFER-V1

Question: does retained whole-payload first-group/two-level preflight remain exact and fail-closed when the live X core keyboard mapping is changed to projections of distinct standard XKB layouts?

Development found that `setxkbmap` returned success on this Xvfb build without changing the server core mapping. Formal testing therefore does **not** claim full XKB layout installation. For each condition, `setxkbmap -print` + `xkbcomp -xkb` resolves the standard layout definition, then a fixture-only `XChangeKeyboardMapping` projection installs Group1 levels 0/1 into a fresh private X server. The candidate under test reads that live mapping unchanged.

Fixed formal order: `us`, `de`, `fr`, `us(dvorak)`. Each condition gets a fresh authenticated Xvfb process and fresh receiver.

Payloads: every printable ASCII code point U+0020..U+007E, one character per trial.

Hard gates per trial:
- if candidate preflight accepts, separate Tk application text must equal exactly the requested character;
- if candidate preflight rejects, emissions must be 0 and application text must remain empty;
- live mapping fingerprint must remain unchanged during delivery;
- physical input must end empty.

Hard gates per arm:
- resolved XKB projection must modify the server mapping when the layout differs from US;
- candidate dependency Git blob must be exactly `35c7375e50f3e0c58f57c8139a6dc8abeef87771`;
- all 95 trials satisfy their gate;
- baseline core mapping is restored exactly at arm end.

Disposition: `TRANSFER_PASS_SCOPED` only if all four arms pass. Coverage counts are observations, not pass criteria. A rejected printable character is not a successful delivery.

Limits: this is Group1 level-0/1 **core-map projection**, not full XKB type/group/AltGr/compose behavior. No Unicode/IME, Wayland, Windows/macOS, model/token, Office, or product claim.
