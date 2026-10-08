# V39 decision 5 pending-frame trace audit

This is an additive retrospective audit of retained allocation `map01-v39-coast-liveness-live-01`. It independently joins typed observations 154, 200, and 204 to exact image observations, verifies the retained PNG pixels against each event's RGB SHA-256, and checks that observations 200 and 204 were captured while decision 5's planner turn was pending.

Run from a checkout containing the retained allocation directory:

```powershell
python audit.py path/to/map01-v39-coast-liveness-live-01
```

The script requires Python 3 and Pillow. It verifies each input file against `retention-manifest.json` before parsing it. A successful run prints a compact JSON audit record.

The trace establishes that sequence 200 (health 51, ammo 38) and sequence 204 (health 51, ammo 38) have exact PNG-backed observation records inside the pending decision-5 turn, after the original user message and before the turn's interruption. The planner protocol shows no additional user message or steer event carrying either observation. The turn ends `interrupted`, and the report marks its answer ineligible.

This does **not** establish what an uninterrupted natural answer would have selected. It does not establish model reaction to the new observations, causal control behavior, physical input state, or satisfaction of any live-game gate. It should be read as a trace-identity and ordering check only, alongside the retained reports and prior failed/synthetic audit history.

