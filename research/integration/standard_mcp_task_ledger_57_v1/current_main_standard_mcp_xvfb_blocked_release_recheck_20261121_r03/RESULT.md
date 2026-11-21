# Standard-caller Xvfb optimized repeats R03

Status: `REPRODUCED_XRES_SUPERVISION_TIMEOUT_3_OF_3`.

Three predeclared optimized-mode attempts against the same source revision and isolated Xvfb image each exited 1 at the standard-caller XRes disconnect assertion. Each worker reached the 150 ms supervision boundary, was retired with exit code -15, returned no result, and classified disconnect as UNKNOWN. The release worker was not attempted. Container final cleanup read A/B/C up on every run.

These repeats establish a deterministic local limitation for this bounded environment/mode, not a reliability rate or a claim that other hosts behave identically. R04 tests the timeout hypothesis diagnostically without changing source files.
