# WSLc image build

Allocation: ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01
Engine: Microsoft WSL Containers (wslc.exe) 3.0.1.0
Build command: wslc build --progress plain --file research/doom/map01_focus_repeat_owner_59_t0_20261002/Dockerfile --tag focus-repeat-59-t0:20261002 <repository-root>
Base: python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
Base image ID: sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364
Result image ID: sha256:865bfbcc86992769ec9b8311a2344b67c664639d96d7cf0d5c407df9c2c500ed
Platform: linux/amd64; container OS Debian trixie
Python: 3.12.15
python-xlib: 0.33
Packages: xvfb=2:21.1.16-1.3+deb13u4; x11-utils=7.7+7; x11-xserver-utils=7.7+11
The build used network to resolve apt and pip packages. Formal candidate and audit runtime are separately frozen as pull=never and network=none. The full, unedited WSLc build log is IMAGE_BUILD.log.

The WSLc kernel warned that swap/cgroup memory enforcement is unavailable. The requested runtime memory value is not claimed as an effective limit. This deterministic Xvfb/XTEST event-order fixture is not GPU-compute-bound; no GPU was requested.
