# S25 WSLc current-main private-Xvfb 3940 ms probe

The current-main standard-caller test completed successfully at a 3,940 ms private X-server pause. The supervisor release receipt arrived at 3,992.386 ms after cancellation admission, leaving 7.614 ms before the 4,000 ms transaction deadline. However, an independent parent X client completed its all-keys-up readback at 5,002.641 ms after cancel start, exceeding the preregistered 5,000 ms bound by 2.641 ms. The 8,502.996 ms late-request horizon showed all keys up and no delayed press.

S25 is classified `FAIL_INDEPENDENT_READBACK_BOUND_5S` (24/25 checks), not a pass. The old and fresh synthetic task oracles passed, but independent release confirmation missed its bound. Public runtime state remains `UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`. Container, image and WSLc session cleanup succeeded. No retry was made.

This is private synthetic Xvfb evidence only, with no claim about physical GUI, real applications, MAP01, efficiency, or reliability. See the preregistration, audit and raw files under `output/`.
