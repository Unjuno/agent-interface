# Guarded Hierarchical Deoptimization (GHD) — Experimental Algorithm Spec

Status: Python experimental baseline candidate. Not a production/Rust ABI specification.

## State per semantic method

- semantic method definition
- target binding
- optimized route
- route dependency guards
- repairable precondition guards
- route heat state: COLD / HOT
- clean-use counter
- postcondition verifier

## Invocation

1. Validate/repair target binding.
2. Evaluate repairable preconditions.
   - If repairable and false: repair locally; do not cool the route.
3. If route is HOT, evaluate route dependencies.
   - If any dependency is false: DEOPT the route before executing it.
4. If route remains HOT, execute optimized route.
5. Verify postcondition.
6. On optimized-route postcondition failure:
   - cool route immediately;
   - execute Universal fallback under verified binding.
7. On Universal success:
   - retain semantic method;
   - accumulate clean uses;
   - after 2 clean uses, recalibrate and reheat optimized route.
8. On Universal failure under a fresh verified binding:
   - escalate failure classification toward semantic invalidation/relearning.

## Invalidation granularity

- focus/precondition failure -> repair precondition only
- geometry/anchor/shortcut dependency failure -> invalidate route only
- target window/process replacement -> invalidate/rebuild binding only
- Universal postcondition failure after fresh binding -> semantic invalidation candidate

## Current constants

- initial method learning: 2 successful uses
- route reheat: 2 clean uses
- verified route dependency failure: immediate pre-execution DEOPT
- verified binding failure: immediate rebind
- semantic invalidation: only after lower layers cannot realize the postcondition

These constants remain experimental and are not yet a stable ABI.
