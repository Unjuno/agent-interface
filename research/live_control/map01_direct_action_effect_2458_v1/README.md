# MAP01 direct action-effect calibration (#2458)

H: a declared ViZDoom action can cross the game-side boundary and produce measurable state or observation change.
T: private Xvfb, basic.wad/map01, one fresh observation, one MOVE_FORWARD action for four tics, one post-action observation, then cleanup.
D: retain exact versions, declared button/variables, reward, pre/post state, position delta, frame hashes, and cleanup.
C: direct engine action only; no X11 transport, model, human tempo, visual-target admission, general effect detection, or end-to-end claim. No retry.
U: PASS only authorizes a later controller/X11 transport experiment; HOLD/STOP remains evidence.
