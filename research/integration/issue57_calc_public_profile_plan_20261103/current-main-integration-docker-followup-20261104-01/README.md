# Current-main Calc composition follow-up 01 — construction failure

The old test now attempted observe and mint, but selected a region extending outside the synthetic observation. The guard refused with `handle region outside observation`, before profile execution or input. Normal and optimized targeted runs both failed this construction check. Raw logs and the exact updated test source digest are retained; no runtime change was made.

A smaller in-frame region was then used in follow-up 02.
