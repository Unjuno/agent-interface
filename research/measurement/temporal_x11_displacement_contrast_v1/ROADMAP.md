# TEMPORAL-X11-DISPLACEMENT-CONTRAST-R1-20260918-012

Issue #1347. One factor only: target red intensity C255/C192/C128/C64.

Construction: nonformal phases {0.125,0.375,0.625,0.875}, two directions, four contrasts, one private Xvfb session =32 pairs/64 frames.
Formal after explicit #60 lease: phases0.00..0.99, two directions, four contrasts =800 pairs/1600 frames; four fresh private Xvfb sessions, each owns25 phase identities and both directions; one supervisor invocation; reruns/replacements/tuning0.

Detection is frozen: R>=32 and R>=4*max(G,B); centroid is red-intensity weighted. Geometry/background/XGetImage/7.3px displacement stay fixed from #1326.

Pre-freeze construction defect retained: python-xlib returned `img.data` as `str` at C64, making `bytes(img.data)` raise TypeError. Repair is representation-only: Latin-1 encode when `img.data` is str, preserving byte values 0..255. Formal remains0.
