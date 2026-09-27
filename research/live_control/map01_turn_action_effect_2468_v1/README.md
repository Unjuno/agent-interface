# MAP01 turn action-effect control (#2468)

H: TURN_LEFT exposes a direct game-side transition where MOVE_FORWARD was held.
T: one fresh basic.wad/map01 episode, one TURN_LEFT action for four tics, pre/post angle and screen hash, cleanup.
D: retain runtime, exact pre/post values, reward, hashes and disposition.
C: direct engine only; no X11, model, visual-target or end-to-end claim; no retry.
U: control successor for #2458/#2417.
