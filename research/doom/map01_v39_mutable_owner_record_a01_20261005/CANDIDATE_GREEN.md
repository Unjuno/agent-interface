# Candidate GREEN receipt

On the isolated successor candidate, the barrier test passed once normally and once under `python3 -O`. The full predecessor candidate suite plus this regression passed 14/14 in normal mode and 14/14 optimized mode. The exact-current-main overlay at `0015aea71eeef36ed53513ace5a952dc9cb265c6` also passed 14/14, 14/14 optimized, 3/3 ExecutorV12 expiry compositions, 10/10 InputOwner compatibility tests, and 2/2 V39 bridge tests.

`py_compile` passed for the candidate bridge, owner, and focused regression. No container was used: this was a short deterministic fake-display test on host CPython 3.14.5. No X server, GUI, game, or OS input was used.
