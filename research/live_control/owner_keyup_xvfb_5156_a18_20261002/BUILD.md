# WSLc image build record

Allocation: `MAP01-OWNER-KEYUP-BRACKET-5156-WSLC-20261002-18`

The image was built locally from `Dockerfile` with `wslc build -t agent-interface-5156-a18:20261002 .`. Base: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Result image ID: `sha256:ba221756a0f848b1b720f519ff7f8b2c1288067abd4bcd2c406d40d9640343d4`.

Build-time package resolution used Debian trixie apt repositories and pip network access. Installed versions observed in the build output: Python 3.12.14, python-xlib 0.33, xvfb `2:21.1.16-1.3+deb13u4`, x11-utils `7.7+7`, xserver-common `2:21.1.16-1.3+deb13u4`. The image was then run with `--pull never`. All candidate, construction and auditor runs used `--network none`.

WSLc emitted its kernel warning that swap/cgroup memory limit capabilities are unavailable. The commands requested one CPU and 512 MiB, but those cgroup limits are not confirmed enforced. Architecture was x86_64. GPU passthrough was not requested because this X11 server-side request-boundary measurement does not use GPU computation.
