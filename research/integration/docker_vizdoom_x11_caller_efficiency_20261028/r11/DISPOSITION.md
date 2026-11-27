# R11 execution disposition

All four preregistered attempts failed before the Python harness could start: the pinned image contains `/usr/bin/python3` but no `python` command. No ViZDoom, X11 input, or task action occurred. No arm was retried. The fixed image was inspected separately and `python3`, Xvfb, Xlib, and ViZDoom 1.3.0 were confirmed present. R12 is a new preregistration with fresh seeds and changes only the interpreter command to `python3`.
