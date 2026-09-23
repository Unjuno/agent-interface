# Environment assumptions

- Linux disposable container.
- Python 3.13.5.
- Python Xlib module at `/opt/pyvenv/lib/python3.13/site-packages/Xlib`, module `__version__ = (0, 15)`.
- Xvfb Debian package `2:21.1.16-1.3+deb13u1`, binary `/usr/bin/Xvfb`.
- Private Xvfb is launched with `-displayfd 1 -screen 0 640x480x24 -nolisten tcp -pn -ac`.
- Because this container has no usable Xauthority file, both fixture and measurement client set `XAUTHORITY=/dev/null`; access control is disabled only on the disposable private Xvfb.
- XGetImage uses ZPixmap and plane mask `0xffffffff` in both arms. Only capture rectangle differs: 320x240 versus 32x32.
- No XTEST or other OS input is generated. EFFECT is a local measurement log only.
