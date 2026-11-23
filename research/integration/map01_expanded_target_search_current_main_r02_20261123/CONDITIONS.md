# MAP01 expanded local target search R02 — frozen conditions

- Frozen source baseline: current `origin/main` `fd3f0f58edd1b77127b84fa1be7757aff9b3b739`.
- Question: does the user's current Windows profile or common game/custom-install location still contain the exact GZDoom executable and expected Doom/Freedoom IWAD files needed to resume the retained MAP01 experiment?
- One read-only filename search; no retry or replacement. Search only the roots listed in `conditions.json` for exact basenames `gzdoom.exe`, `doom2.wad`, and `freedoom*.wad`.
- Use `rg --files --hidden --no-ignore`, exclude `.git` directories, capture stdout/stderr bytes and exit status, stop at 90 seconds if the bounded scan has not finished.
- Do not inspect file contents, launch or focus an application, send input, install/download assets, start Docker/WSLc, or consume a model allocation.
- A positive result is only a candidate path. It does not authorize launch or prove ownership, provenance, hash, task setup, or suitability. A negative result is scoped to these directories and names, not a whole-disk search.
- No target task is started by this preflight. All conclusions are limited to target discovery.
