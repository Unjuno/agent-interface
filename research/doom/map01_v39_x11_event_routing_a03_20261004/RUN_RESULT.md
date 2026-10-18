# A03 STOP: X11 event-routing control

The candidate exited 1 before launching Xvfb because its required output directory `results/A03` already existed from the preflight check. No XTEST or InputOwner operation ran, and the independent auditor was not invoked. The command stdout, stderr, exit status, and STOP record are retained under `results/A03/`. The event-routing experiment was not performed. This allocation will not be retried.
