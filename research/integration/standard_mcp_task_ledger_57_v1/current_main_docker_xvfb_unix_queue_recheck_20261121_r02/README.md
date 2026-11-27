# Docker private Unix-socket Xvfb queue recheck R02

This finite experiment uses the existing `agent-interface-xvfb-mcp:late-input-r19`
image, which was checked read-only for Python 3.11, Xvfb, xauth, and Python-Xlib.
The repository mount is not used: only the two hash-pinned source files are copied
into this packet and the packet itself is mounted read-write. The container has no
network, a read-only root filesystem, and a private X11 Unix socket directory.

Run exactly once in normal mode and once with `-O`; each attempt has its own run
folder and cannot overwrite an existing result. The result's late-key readback is
the queue discriminator; unittest PASS alone is insufficient.
