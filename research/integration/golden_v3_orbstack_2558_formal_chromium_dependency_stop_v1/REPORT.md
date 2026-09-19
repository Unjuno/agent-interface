# #2558 formal Chromium route dependency stop

Date: 2026-09-20 Asia/Tokyo

## H/T/D/C/U

- H: after materializing the exact main commit with a blobless sparse checkout, the official Chromium integrated route can run in a container if Chromium/Xvfb dependencies are available.
- T: build a pinned arm64 Debian container with Chromium/Xvfb and the required Python packages, then mount the exact main tree and run the frozen `preregister_integrated_efficiency_live_v1.py` / `run_integrated_efficiency_live_v1.py` entrypoint.
- D: source materialization succeeded at main commit `9c9d7cf2bea50e47638c63effa72a5059fdb4e58`; required official Python sources were present. The Docker image build stalled after starting a 214MB Debian dependency download for over four minutes with no image produced. A separate ephemeral container using the existing image stalled during `apt-get update/install chromium xvfb xauth` for over two minutes with no package completion. No official Chromium allocation, model call, or formal task metric was counted.
- C: `STOP_FORMAL_CHROMIUM_DEPENDENCY_FETCH`.
- U: provide a cached/prebuilt arm64 Chromium image or a working package mirror, verify the exact preregistration source hashes, then execute the official route once and retain its first complete/failure result.

This is a formal-route infrastructure stop. It does not invalidate or alter the successful fresh Docker persistent and repair experiments already merged for #2558.
