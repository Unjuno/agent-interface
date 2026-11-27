# Controlled leading-digit occlusion and X11 release

One fresh 2026-11-27 WSL/Xvfb trial displayed a retained 100-health MAP01 screenshot in an isolated synthetic window and held an XTEST key. A deliberately injected 3×38-pixel black stripe obscured part of the leading digit. On the same X-server capture, the old reader returned observed `0`, while the candidate returned `UNKNOWN` with `unverified_leading_blank`. The existing signal guard requested a new decision without granting input authority. The test explicitly cancelled the lease; the input owner recorded key-down before key-up, key-up afterward, and verified neutral release. The service retired.

This is a single controlled synthetic-display trial. The test harness performs the cancellation; it does not prove an automatic end-to-end V39 controller cancellation, natural game occlusion, a real model call, a physical keyboard, or a latency guarantee. A digit fully replaced with identical background remains indistinguishable from a genuine blank in one image. The separate draft-then-merged code change is PR #10599.

`raw/` retains the registration, capture PNGs, driver, owner/guard events, service logs, outcome and original seal (SHA-256 `bcf99f8d7be0126358d0e2a2e0b248d8296ef53617c9d6d799178709c3ecfd56`). `source/` contains the exact reader and guard bytes needed for replay, pinned by the registration and source manifest. No game asset is bundled or downloaded.

With Python 3.11+ and compatible Pillow, NumPy and the original pinned Freedoom WAD already available, run:

```sh
python audit.py --wad /path/to/freedoom2.wad
python -O audit.py --wad /path/to/freedoom2.wad
```

The audit checks the original seal and each retained byte, source/WAD pins, the exact pixel difference, both reader results, guard output, release receipt and service outcome. Local normal and optimized runs passed; an optimized run against a modified copy of the occluded PNG failed as expected. This does not rerun the original live X11 experiment.
