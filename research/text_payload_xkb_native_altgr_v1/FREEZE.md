# Native XKB AltGr delivery freeze

Task `XKB-XDUMMY-NATIVE-ALTGR-DELIVERY-20260916-001`, Issue #399.
BASE `b3bc631d2c6dfae8586bb28abdc9eb2002bb624b`.
No formal server or XTEST payload has run under this task at publication of this freeze.

Formal: three fresh Xdummy/Xorg servers on :190/:191/:192, 16 frozen payloads each, same German XKB SHA. No projected core-map mutation and no synthetic Mode_switch binding. Candidate parses live full-XKB readback, whole-payload preflights direct Group1 levels 0..3, then uses native Shift/RALT keycodes. Dead-key/Compose paths remain ineligible and must refuse with zero emissions.

Source SHA-256:
- `candidate.py` `c732913207ec7fbf96ebe9cb05b63e1a9ee8715420f64a4fdc0898a95ed860f7`
- `run_arm.py` `01b989c792bdb9a496c3563659fec495d3058fad53ba202b839b21225e88693f`
- `run_block.py` `68449879e191d87cb6894e31701ce2a6d1f237630d0be061252108567cfa63d6`
- `audit.py` `91a8aa7bf117233050eabe0878e80ec14d16335706abaf780a4212ab640968c7`
- `receiver.py` `984f86bc1651ec6c2b718b34a9372603efd1f12b0c26f838e083f5e46b90a538`
- `schedule.json` `a9448f3b4273e5709b05793fc1ea437eadda1af36e7e90a19b925e2f3f1bff0a`
- `environment.json` `3f7443e866613e053a47db71b361637d2e389ae4b1e38b3cbd67987139273e37`
- `test_candidate.py` `fdabbd9ecbb5d127e0236546ad71bc37c59b0d754882e4270dc58387a651fa36`
- `plan.json` `b316114033bbc4f22eb03e569b51470b7527f13a0ca95bb7fe4c282440309bd7`
- `prereg.json` `23d604c6387b5db9ff24321154dc11dee6b942c9cba82138d3e7fc14ffc23d20`

Decision: PASS only if all 36 eligible trials deliver exact receiver text, all 12 ineligible/dead-key trials refuse with zero emissions/empty receiver, map/modifier/full-XKB identities remain invariant, release is empty, and independent audit passes. No rerun or payload tuning.
