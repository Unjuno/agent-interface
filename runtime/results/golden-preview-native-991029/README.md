# Golden Desktop v3 native Windows Codex acceptance

The supported-host acceptance and its live audit passed on source revision `e90f35e5866f31c9571cf5d82bed617d81f1ddfe`. This was one fresh allocation with seed `991029` and no automatic retry.

The run used Ubuntu 24.04.3 on WSL2, Python 3.12.3, and headful Chrome for Testing 156.0.8078.4. Windows Codex CLI `0.171.0-alpha.13.2` provided schema preflight over Exec and two grounding turns over one persistent App Server session. The requested model was `gpt-5.6-luna` at `low` effort. A private Xvfb display with Xauthority ran under a bounded systemd user service. The display, window manager and service cgroup were retired after completion.

All six synthetic form submissions matched the independently checked task tokens. The route sequence was cold, reuse, reuse, repair, reuse, reuse. The live audit verified input release for all 57 terminal programs, zero pointer admissions against the old target, and one successful repair after the layout change. The schema preflight and the App Server each had a Windows Job receipt with zero active processes at retirement.

| Provider usage field | Tokens |
| --- | ---: |
| Input | 30,716 |
| Cached input | 9,600 |
| Cache write input | 0 |
| Output | 472 |
| Reasoning output | 127 |

All three calls reported all five fields. Cache write zero was explicitly reported. The two grounding calls used two images in total.

[The machine-readable summary](live-summary.json) records the run conditions, aggregate observations, and SHA-256 digests of the local originals. The manifest was verified against all 302 listed local files. The full execution and provider records are retained locally. Replaying the live audit requires those originals.
