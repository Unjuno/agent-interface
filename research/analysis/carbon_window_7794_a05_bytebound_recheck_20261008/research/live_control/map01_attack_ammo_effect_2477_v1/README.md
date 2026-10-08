# MAP01 ATTACK ammo calibration (#2477)

H: the retained attack-response evidence is reproducible with explicit AMMO1.
T: freedoom2.wad/MAP01/PLAYER/RGB24, seven-button declaration including ATTACK, one `[0,0,0,0,0,0,1]` action for one tic.
D: retain pre/post AMMO1, reward, frame hashes, exact fixture and cleanup.
C: direct engine only; no X11/model/general effect/end-to-end claim; no retry.
U: calibration gate after #2458/#2468/#2472.
