# A01 construction STOP

The frozen runner reached the baseline child but did not receive its expected `ready` event. Source inspection found the bootstrap rewrote `sys.argv` using `sys.argv[2:]` and dropped the first session argument (`--out`). The child therefore exited during V15 argument parsing before the fake session initialized. The runner terminated at its readiness gate and did not execute a baseline/candidate acceptance pair. This is a harness STOP, not a baseline outcome or evidence against the poller. The A01 result does not satisfy its decision gate. The runner failed to retain the child's stderr on this STOP; the failure cause is reconstructed from the frozen runner/bootstrap source, not claimed from raw child output. No game, model, GUI, X server, or OS input ran.

A fresh A02 package contains the repaired argument forwarding and will execute the pair once. A01 frozen files and hashes remain unchanged.

## Correction from A02 source inspection

The more precise defect was in the runner invocation: it omitted the selected V15 script path when launching the bootstrap. Consequently the bootstrap treated `--out` as its script path and then sliced session arguments. The earlier description that V15 argument parsing itself was reached was unsupported and is withdrawn. Child stderr was not retained, so no exact exception string is claimed. The construction STOP and absence of input/game effects remain accurate.
