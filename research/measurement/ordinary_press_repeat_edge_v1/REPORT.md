# Repeated ordinary key-down admission alias — construction result

Decision: `PASS_REPEATED_PRESS_ADMISSION_ALIAS_SCOPED`.

Pinned source identity: `research/live_control/input_owner_v10.py` Git blob `341b3c01649943ddaad5f28431a792c4889cc36e` at BASE `4b106a9b549fc3499d39ef2c7e3367d95a6c736c`.

The exact current v10 ordinary `down` path has no same-key already-held rejection analogous to `button_down`. After the existing active-lease guards, it assigns the key to `held`, emits one `KeyPress`, syncs, and returns only `{event,key,admitted_ns,input_ack_ns,valid_until_ns}`. The returned admission carries no pre-held/physical-pre/new-hold discriminator.

Construction isolated that information boundary with matched hidden modes and deterministic public clocks. Across 100,000 seeded matched pairs, `FIRST_DOWN` had `hidden_new_hold=true` and `REPEATED_DOWN` had `hidden_new_hold=false` in every pair, while the complete public admission dictionaries were identical in all 100,000 pairs. Both modeled paths emitted one press and one sync, matching current control-flow shape. Fixed controls 8/8 passed: valid first/repeat, different-lease conflict, unavailable key, sync failure, reversed clock, malformed key, and absence of forbidden pre-state fields.

This is an information-flow result, not X11 effect evidence. It does not establish how a real X server/application treats repeated XTest KeyPress. It establishes only that current `input_admission` cannot by itself prove a fresh physical DOWN edge. #998-style owner-thread pre/post physical sampling is therefore required before a fresh actuation generation or physical-down interval is inferred.

Construction seed: `100120260917001`; result digest `a9b6710727e024be8704c005ff94a4868b9512e93b2d310ab40521613d966b10`; Python 3.13.5; no formal/live allocation and no task input.
