# R37 result — Computer Use screenshot target mismatch

Disposition: STOP_CUA_WINDOW_SCREENSHOT_MISMATCH_BEFORE_MCP. The single allocation is consumed; no retry was made.

Computer Use accessibility state identified the R37 source fixture, but its screenshot displayed the retained R35 fixture title and contents. The target could not be visually tied to the expected R37 HWND, so no click, activation marker, public observation, or input was issued. The runner was stopped while waiting for activation. The R37 fixture remains open under the stop rule and the durable fence is clear.

This exposes a computer-control targeting/evidence mismatch in this environment. It does not establish a runtime behavior result. A later attempt must first restore one-to-one screenshot/HWND window binding and verify that mapping independently before any action.
