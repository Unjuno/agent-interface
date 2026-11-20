# A02 — packaging STOP

The one frozen candidate invocation exited 1 before it loaded source locks or imported production modules. The container ran `python -B /src/candidate.py`; that script immediately required `/src/FROZEN_INPUTS.json`, but the freeze had been kept at the package root outside the read-only `/src` bind. The exact traceback is retained in `CANDIDATE_CONTAINER.log`; container configuration and exit status are in `CANDIDATE_CONTAINER_INSPECT.json` and `CANDIDATE_EXIT_CODE.txt`.

No candidate result was written; the independent audit was not invoked, as frozen. No production import, session route, fake display, release schedule, game, model, or input occurred. This is a harness packaging STOP, not evidence about V15 release order. Do not retry A02. A new run ID is required for a freeze-path correction.

The complete current-main source closure and original candidate/auditor locks remain in `FROZEN_INPUTS.json`; the container source mount was read-only. The memory-without-swap warning from WSLc is retained in the raw log and means configured memory is not evidence of a no-swap enforcement bound.
