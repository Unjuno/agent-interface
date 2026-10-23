# Rootless local xterm qualification — R01

The Ubuntu distro had Xvfb/Xlib but no available xterm, Calc, browser, editor or game executable among the explicitly queried candidates. To qualify an actual external GUI application without changing the system package database, three exact Ubuntu packages were downloaded and extracted under `/home/user/.cache/agent-interface/xterm-20261023-r01/root`:

- xterm `390-1ubuntu3`, package SHA256 `3541b6956d6c4be71db7b66ec91985bd5eb128fb130e806f1c879f9d94a97c72`.
- libxft2 `2.3.6-1build1`, SHA256 `b4f4f3255c0b8773b260c61cbe20ee7c63799cfc0e4e389fa58375dd480b093a`.
- xbitmaps `1.1.1-2.2`, SHA256 `be00b7ea28e33a6e8342ddc0608dd32d9c255a329b57fb7589c650fecd5fe58c`.

The actual `.deb` bytes matched the cached Ubuntu apt metadata before extraction. `apt-metadata-*.txt`, download stdout/stderr, command exit receipts and `setup-receipt.json` preserve provenance/paths/hashes. The original `.deb` files and extracted bundle are retained in that persistent user cache; this packet does not vendor those third-party binaries. The extracted xterm executable SHA256 is `5415c1445d44e4c347fe51e30dd8f014de7e489873cfc82fe32af628dc01d4c4`.

With its local libXft library path, `ldd` resolves all dependencies; `-version` and `-help` exit0 with DISPLAY explicitly unset. These are input-free construction checks, not a GUI task outcome. The [separate frozen public-MCP trial](../xterm_public_task_20261023_r01/README.md) pins53 actual native binary/library hashes and supplies the live application evidence.

No global package install/update, Docker/WSLc operation, Windows desktop input or formal trial occurred during setup. Raw apt output retains its ordinary CLI warning and trailing blank lines unchanged. The packet-only attributes preserve raw bytes; whitespace suppression applies to these raw `.txt` records only.
