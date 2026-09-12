# Real App Benchmark v1

Environment: Debian 13, Xvfb 1280x800x24, Openbox, Python Xlib/XTEST.

B0: sequential-full, 100 ms fixed settle after every logical op + full-screen observation.
B1: sparse-reactive, X11 transition barriers, 1 ms TEXT pacing, 2 ms ButtonPress->motion barrier, observations only where required.

| App | B0 success | B1 success | B0 p50 ms | B1 p50 ms | p50 reduction | B0 MPix | B1 MPix | obs reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| xterm | 8/8 | 8/8 | 218.9 | 16.2 | 92.6% | 3.072 | 1.024 | 66.7% |
| chromium | 8/8 | 8/8 | 342.1 | 166.0 | 51.5% | 4.096 | 1.024 | 75.0% |
| calc | 7/8 | 8/8 | 550.7 | 114.8 | 79.2% | 6.144 | 2.048 | 66.7% |
| inkscape | 4/8 | 8/8 | 1376.9 | 168.3 | 87.8% | 4.096 | 1.024 | 75.0% |

## Microbench findings

- LibreOffice Calc TEXT burst: char gaps 0 ms and 0.1 ms: 0/12 exact; 0.25 and 0.5 ms: 1/12; 1 ms and 2 ms: 12/12 exact.
- Inkscape drag press dwell: 0 ms: 18/20; 2 ms: 20/20; 5 ms: 20/20 (same process microbench).
- Chromium localhost/file URLs are blocked by container organization policy, so the browser task uses browser-chrome navigation to chrome://version.

## Interpretation

The real-app suite falsifies the assumption that XSync alone is sufficient as an application-level delivery barrier. Correctness depends on small, operation-specific consumption barriers: TEXT pacing and pointer-press dwell. Fixed 100 ms sleeps are both slower and still less reliable.
