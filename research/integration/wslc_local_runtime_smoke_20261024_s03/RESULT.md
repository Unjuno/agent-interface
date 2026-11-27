# Result S03

**Status: HOLD/UNKNOWN — session creation was unavailable through this CLI path.**

The pre-created, empty attempt-owned storage path was passed to `wslc system session enter --name`. The command exited 1 with `ERROR_PATH_NOT_FOUND` and reported no WSLc session at that storage path. No session process persisted; no image pull or container run started. The exact command, output summary, and status are recorded in `run/session-start.json`.

S03 is closed without retry under its preregistered failure rule. The `enter` CLI help suggested that it creates a nonpersistent session, but the observed service response requires a session already associated with the storage path. S03 supplies no WSLc execution or computer-control pass evidence.
