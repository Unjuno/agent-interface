# Bounded-error interval TTC (Issue #8157)

Construction-only A01. Base main: fd4f9e4533aa5baa5952e89cd830c98b26e7c537. No candidate corpus or independent audit has been invoked.

Method: input two positive apparent radii, increasing timestamps, and declared absolute per-frame radius bound e. Feasible radii are [r-e,r+e]. Under local constant radial velocity, TTC=r2*dt/(r2-r1). Enumerate feasible rectangle corners. Return UNKNOWN if radii can be nonpositive, expansion is not guaranteed, or inputs are invalid. YIELD only if the whole TTC interval <=2.0s; CLEAR only if wholly >2.0s; otherwise UNKNOWN. This is not a scene-semantic claim.

Construction tests exercise arithmetic and fail-closed boundaries only. Formal frozen data remains candidate 0, auditor 0. Requested corpus: seed 8157; ten profiles x 20 sequences; 12 observations; nominal 30Hz; 0.5px bound; approach, pass-by, stationary, iid/correlated error, irregular/dropout, acceleration/deceleration, occlusion, identity swap, understated bound. Oracle stays auditor-only. The matched false-YIELD operating point, simple-cue reproduction, lead rule and mutation scorer still need a complete preregistration before candidate/auditor invocation. No GUI/model/input/game/runtime integration.
