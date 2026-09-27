# Text delivery capability model v1 — retained offline result

**Result ID:** `text-delivery-capability-v1-20260916-01`  
**Source/plan freeze:** `1eb99b0e831ad0236b06b26548a114e6719a7b70`

## Disposition

**PASS_OFFLINE_CAPABILITY_MODEL / HOLD_SHARED_CONTRACT_PROMOTION**.

The source-frozen offline selector passed 12 deterministic tests and 4,096 exhaustive capability-state × side-effect-budget cases with zero safety violations. No GUI, OS input, model, provider, or network call occurred.

## Evidence-derived decisions

- transparent ASCII request -> `direct_keys`;
- transparent Unicode request -> **no eligible route** under current X11 evidence;
- Unicode request that explicitly allows clipboard content/owner/TARGETS mutation -> `clipboard_utf8`;
- Unicode request that allows only global-keymap mutation -> **no eligible route**, because retained keymap-remap semantics are not eligible and global-keymap mutation is ranked high-risk;
- unknown and permission-required accessibility/IME routes never silently become eligible;
- if a future accessibility route is both supported and exact and its side effect is explicitly allowed, the model can select it ahead of clipboard lowering;
- even if keymap remap were later exact, its global-keymap risk ranks it behind the retained clipboard route when both are allowed.

## Why this matters

The prior Unicode experiment proved that durable semantic success alone is insufficient for transparent generic text: clipboard UTF-8 paste scored exact in Writer and Calc but changed clipboard ownership. This model keeps semantic text intent separate from lowering-route capability and requires a caller to authorize side effects before a route can be selected.

## Controls

- 5/5 frozen source blobs matched before formal execution;
- 12/12 unit tests passed;
- exhaustive cases checked: 4,096;
- safety violations: 0;
- formal reruns: 0.

The outer container display appended `TERM environment variable not set` after child completion. Internal unit/experiment receipts and audit are zero/PASS; the result ID was not rerun.

## Limits

This is an offline candidate interface model. The side-effect cost ordering is a research hypothesis, not a shared ABI. Accessibility set-value and native IME remain hypothetical until real platform evidence exists. No portable-contract or shared-runtime file is modified.

## Successor

Use platform evidence to replace hypothetical route states with measured capabilities. Only after at least one non-clipboard Unicode route is independently validated should the common text-delivery interface be considered for promotion into shared semantics.
