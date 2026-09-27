# MAP01 / ViZDoom observation preflight (#2446)

H: a pinned container can reach one real MAP01 observation through private Xvfb.
T: install the minimum runtime, launch private Xvfb, initialize ViZDoom basic.wad on map01, reset once, read one screen buffer, and close.
D: record versions, display, Xvfb, launch/reset/observation/close statuses and stderr. PASS requires a non-null real screen buffer.
C: no model, network service, user desktop, action schedule, visual-target claim, effect/consumption claim, or end-to-end claim. Missing dependencies and launch failures are retained as HOLD.
U: this only gates the next game-boundary experiment; it does not modify #1637, #2417, or historical results.
