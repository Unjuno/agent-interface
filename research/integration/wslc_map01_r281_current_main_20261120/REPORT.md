# R281 MAP01 expiry, re-observation, and task effect

Disposition: verified one expired intent suppressing its delayed action, followed by fresh re-observation and one correctly adjudicated attack.

Frozen against main 381a21ace42891c2cd1e9cff3e231bec763ec2ba; 41 current-main Git blob IDs recomputed and matched. Fresh WSL2/Xvfb MAP01, seed 281, skill 1.
Initial typed baseline: sequence 1, ammo 50, health 100. Old intent held Right with a 1200 ms request and 250 ms validity, then contained a delayed Space action. Only Right was admitted. The expired owner receipt was verified empty and preceded terminal status expired; the delayed Space step never started.
After the expired terminal, distinct ID R281-recovery produced fresh post-expiry observation sequence 4 (ammo 50, health 100) and completed with verified release. A third, distinct ID then admitted exactly one Space attack using sequence 4. Typed sequence 7 reported ammo 49 and health 100.
All terminal releases and final owner close were verified neutral; runner process exit 0. Player alive; no MAP01 exit.
No standalone input_released event for expiry (count 0); the independently recorded owner receipt is preserved and embedded in terminal. This is one bounded end-to-end recovery/action trial, not full map completion or integrated efficiency comparison.

Raw archive SHA-256: 248662bc4109662568b2a8ca09a0efe98c97b78d727474a3ccee9be3eca9738e.

Local regression verification: current-main cancellation-release suite passed 8/8 under normal Python and 8/8 under -O. See LOCAL_TESTS.md.
