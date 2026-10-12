# A13 runtime setup

Xvfb and Python-Xlib were extracted into an external scratch directory; no apt package was installed system-wide. A13 candidate ran as the unprivileged WSL user inside a root-created private network namespace. Loopback was enabled. `xkbcomp` was linked at `/usr/bin/xkbcomp` for the run and removed by the runner's EXIT trap. The read-only `/tmp/.X11-unix` was not changed; Xvfb used `-nolisten unix`. X11 TCP access stayed inside the network namespace.

Exact downloaded runtime packages:

- `libfontenc1_1%3a1.1.8-1build1_amd64.deb` SHA-256 `0c5d57211cac9659e7f4c856f5e1922c4a522fe8bcf5776e9707b2811f965702`
- `libxfont2_1%3a2.0.6-1+deb13u1build0.24.04.2_amd64.deb` SHA-256 `e2ed49a20ccff6ffa52719a6cd118538e24c434d9035acd7fb736e7e4f8d6485`
- `libxkbfile1_1%3a1.1.0-1build4_amd64.deb` SHA-256 `22ac5b7dca740e606261cebdfaf1a07738e92ad3d123570694374ddb4d5afea2`
- `python3-xlib_0.33-2_all.deb` SHA-256 `affdff5765d5ea3f1824a46bf83cb07666e8f0b94a90deea240c02a6083657c9`
- `x11-xkb-utils_7.7+8build2_amd64.deb` SHA-256 `69df4191e165f8b89d067f6234fcce89a4923d27d1e66dd92e6d63d6da93cdb0`
- `xserver-common_2%3a21.1.12-1ubuntu1.8_all.deb` SHA-256 `5720e7995c3b546927046f63bb4a344773b27850379c4b2694edf279025ad772`
- `xvfb_2%3a21.1.12-1ubuntu1.8_amd64.deb` SHA-256 `712429d9342c7d6cef63afb33ccfcd2bd477a69371b5c9941a9c6dde31a4cd3c`

Runner source for the retained invocation: [`run-a13.sh`](run-a13.sh). It points to `/mnt/d/codex-research/v39-xvfb-a09-env-20261012`, the local external scratch directory used on this host. The one-shot A13 output already exists; do not invoke it again. Future runs require a new frozen ID and unique display.
