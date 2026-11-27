# R07 — repeat the focused suite after the R06 timing error

R07 repeats the same four focused modules after preserving R06's normal-mode
error. The standard CLI forwarding and prerequisite rejection tests are
included. Both runs pass **107/107 tests**: normal in 42.624 s and optimized
Python in 43.897 s. Raw stdout/stderr and exit codes are retained beside the
conditions and source fingerprints.

R06's single normal-mode error remains part of the record; its isolated test
passed, and R07 is a separate successful repeat, not a replacement of that
outcome.

This remains Windows CPython 3.11.9 with deterministic Fake X. It does not
validate live Xlib/Xvfb behavior, blocked-live-platform-I/O release, delayed
request exclusion, independent product task success, recovery, MAP01, physical
desktop control, matched efficiency or reliability. No WSLc or Docker
allocation was used.
