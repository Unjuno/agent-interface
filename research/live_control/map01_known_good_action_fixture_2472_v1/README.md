# Known-good ViZDoom direct-action fixture (#2472)

H: the repository's existing freedoom2/MAP01 PLAYER/RGB24/four-vector fixture exposes a direct action transition.
T: one fresh episode, one TURN_LEFT `[0,0,1,0]` action for four tics, pre/post frame hashes, cleanup.
D: retain exact fixture and outputs; expose `ANGLE` and require a nonzero
action-specific angle delta. A changing rendered frame alone is not sufficient.
C: fixture reproduction only; no X11, model, target admission, general effect or end-to-end claim.
U: separates #2458/#2468 fixture failure from direct-action availability.
