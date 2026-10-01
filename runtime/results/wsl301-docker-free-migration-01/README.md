# Docker-free WSL migration 01

Source c0148cd5781b8ec95ef5eb71b4657e5880e40c40; installed WSL package 3.0.1.0,
Ubuntu execution version 2, kernel 6.18.40.1-1. The existing native integration
runner passed 383 protocol and 190 harness tests in Ubuntu without Docker.
Full logs and runner hashes are retained. Total wrapper elapsed time was
31.841046949 seconds, not a matched iteration speed comparison.

Docker Desktop was gracefully stopped after Docker ps showed zero running
containers. Existing stopped containers/images/volumes were preserved. Automatic
startup was already false. docker-desktop became Stopped; Ubuntu remained Running.
The stop CLI remained waiting after the backend stopped; its lifetime is recorded
separately and is not a failed native test or permission to repeat shutdown.

One WSLc container used existing Python image ID
sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4,
with network none, 512MiB configured memory, one configured CPU and a read-only
source bind. Portable CLI help and dependency doctor exited 0; inspect independently
records exited/ExitCode 0 and read-only mount. Pillow/Xlib/MCP were absent and
NO_INTERACTIVE_DISPLAY was reported: this is a portable CLI diagnostic smoke,
not an X11/MCP or GUI validation. No model or input was invoked in this smoke.
The archive hash is af8500d6902b3df80c5129213203ac6fc4bf7f39eba6d4291b8188d6efbb8122.
The host warned swap-limit enforcement unavailable; no combined cap is claimed.

Windows initially reported 398772KiB available physical memory, then 2124336KiB
after graceful Docker stop, then 720708KiB with concurrent activity. Those are
point observations, not attributable peak-memory savings. WSLc had a preexisting
session; it was not terminated or globally reconfigured. Other Ubuntu Python
servers and Git operations remained running. No WSL restart or global .wslconfig
edit was performed. Provider usage and matched speed/memory improvements are
unavailable, not zero. Frozen historical Docker studies were not converted.
