# Mindustry repeat fixture protocol v1

Task `MINDUSTRY-REPEAT-FIXTURE-PROTOCOL-20260917-001`, Issue #868, base `c833289b3a632c69087e8b51209f92a8eddda707`.

H: a benchmark-private checkpoint -> independent score -> reset -> reset witness barrier can keep one Mindustry process alive across A/A/A/B/B/B without exposing oracle/reset authority on the controller channel.

T: candidate mod source + benchmark coordinator contract + pure deterministic protocol emulator. Geometry mutation is one benchmark-private boundary after A3 reset witness and before B1 ready; existing X11 resize mechanism is reused conceptually and not reimplemented.

D: PASS only if good trace order is exact; failed score cannot reset; next ready cannot precede reset witness; controller checkpoint/reset attempts reject; exact target+copper reset is present in candidate source; private records never enter controller projection; all controls fail closed; JS syntax/Python compile and independent audit pass.

C/U: source/protocol closure only; no live engine, GUI, X11, model, token or latency evidence.
