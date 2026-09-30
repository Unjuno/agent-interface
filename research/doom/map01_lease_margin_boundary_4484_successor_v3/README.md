# Issue #5062 — real AF_UNIX Docker Desktop lease-margin test

Pre-registered environment: Ubuntu 24.04.4 LTS on WSL2, Docker Desktop Engine 28.5.1 Linux/amd64. Frozen sources come from repository commit `defb4b5b27d6e2faf39c7d8a4a08dfa279ca0bd6`.

The experiment executes the unchanged `_LeaseClockStdin` AST node from the frozen controller, with its three probes transported using the production `unix_json_deadline.exchange` over AF_UNIX to the Docker server running the production `Lease`. Cases: 5.000s, 5.249s, 5.250s, 6.000s, 31.000s. One case block only; no retry after any case starts.

Observed: 5.000s held locally; 5.249s, 5.250s, and 6.000s were submitted and accepted; 31.000s was submitted and rejected by the production 30s horizon. This is `FAIL_PREREGISTERED_PREDICTION` because 5.249s was predicted to hold. Actual probe latency was shorter than 249ms, so more than 5s remained at the unchanged admission check. The preregistered prediction is preserved; no threshold was adjusted after observation.

No game, model, GUI input, or internet access is involved. Docker has no network; source mounts are read-only and only private socket/evidence paths are writable. The 120-sample study from #3886 is not repeated.

Raw observations, host runner, raw-only independent audit, run record, and pre-case STOP history are stored beside this README. A PASS for clock translation mechanics is not claimed: the formal prediction failed even though all accepted deadlines respected the lower-offset bound. This is one environment session, not a timing distribution or MAP01/game/model result.

