# A16 run record

Local final preflight: one invocation, two tests passed on CPython 3.11.9. No earlier failed run.

WSLc 3.0.1.0 final run: pending, exactly one invocation after freeze. Requested constraints: `--network none --cpus 1 --memory 512m`; pinned Python base image from the freeze. The fixture begins with source ammo 6, and both arms receive a newer paired typed observation while the planner turn is pending. Ammo 4 is above the cover floor 1: event remains soft, turn answer stays eligible, and returned minimum-5 fire is rejected. Ammo 0 crosses the cover floor: monitor invalidates, adapter interrupt is requested before fake wire completion, and adapter marks the completed answer ineligible.

Synthetic client/response and authored observations only. No game/model/GUI/OS input/executor or physical release. This does not establish live safety or control success.
