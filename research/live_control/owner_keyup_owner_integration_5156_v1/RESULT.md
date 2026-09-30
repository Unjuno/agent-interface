# Allocation 03: per-key release request brackets in additive owner v11

## Result class

Construction-only fake-Xlib integration check. This is not a formal X11 experiment, does not establish a physical key-up, and does not grant input authority. No GUI, real input, Docker, GPU, or language model was used.

## Hypothesis and method

For the additive copy of `InputOwner` v10, record one `owner_key_release_bracket` per successfully requested key release, with monotonic request-start/request-return timestamps and the return timestamp of the existing XSync. Explicit `up` gets its own XSync; aggregate owner cleanup retains its existing single shared XSync. A failed XTest request or XSync must not publish a successful bracket for that path. v10 remains pinned and unchanged.

The test imports `input_owner_v11` against a deterministic fake Xlib/XTest implementation, exercises the actual owner thread via down/up and aggregate release calls, and inspects requests, sync counts, records, and neutral fake key state.

## Verification

Command: `py -3.11 -B test_owner_integration.py -v` (from this directory with `PYTHONPATH=..`).

PASS: 11 tests: explicit-up event identity and brackets; two-key aggregate cleanup emits two keycode records sharing one XSync timestamp; request/XSync failures emit no explicit-up success bracket; fatal owner-thread release error fails closed; cancellation after one admitted key releases that key and rejects the next; stale intent cannot release another intent's held key; inverted timestamps remain recorded but fail ordering; the pinned v3 transition wrapper injected with v11 produces a caller receipt containing the owner bracket; raw-only auditor accepts a valid joined record and rejects ordering/authority/physical-claim corruption. Fake key state is neutral after cleanup cases.

`git diff --ignore-space-at-eol --check` passed for the production-source changes. The source diff against the pinned v10 copy is limited to measurement bracket records around the existing release requests/XSync. AST audit confirms `InputOwner.__init__`, `call`, `close`, and `_thread_main` are unchanged. No owner admission, focus/lease policy, request ordering, return value, or X11 statement of physical outcome was intentionally changed.

The raw-only auditor is `audit_owner_release_brackets.py`; it consumes JSONL and checks identity presence, integer timestamp ordering (caller start <= owner request start <= owner request return <= shared XSync return <= caller return), and both non-authority flags. It does not infer missing timestamps or rewrite failed records.

Input source pins (SHA-256): v10 `CEAE7D9983CD0BA13A35E01CE2CE7DBBF03A0397B23DDC123B0110B4D4DE670B`; v11 `B80056D407487A7C319FB6008D94075114B8C67AC3D9B193627D24730EB359BF`; transition wrapper v3 `5FFDBB3679451FEFDC3836917D43D924F0F43C8082D21327207ECEFBD87F5BE6`; executor v3 `EA3FA8C9751A6A41B4814AD6E0D03BEC85166765B0A41D2488A51750D17B3A4A`.

## Limitations and stop reason

Fake Xlib verifies software integration only; it does not validate X server scheduling, real display failure behavior, physical keyboard state, timing quality, or any end-to-end action. There is no assertion that keyup occurred physically. X11 formal validation remains unspent as pre-registered, and shared-container allocation/clearance remains unverified. Do not run the formal X11 fixture until that lane is explicitly available. This allocation does not close the broader issue or roadmap item.

## Integration

Files are isolated under `research/live_control/owner_keyup_owner_integration_5156_v1/`. `input_owner_v11.py` is an additive copy; `input_owner_v10.py`, transition wrapper v3, executor v3, and lease are pinned inputs, not modified by this allocation. The integration test supplies fake Xlib and explicitly injects v11 into the pinned v3 wrapper; it exercises software interfaces only.
