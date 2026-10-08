# Live pending→digest resume integration

One primary-assistant private WSL Inkscape allocation seed991115, max2stages.
Use a viewed rectangle edge, wait50ms, Right repeat18, wait50ms, Ctrl+S,
finish_after=true. Client timeout0 intentionally returns without waiting.
If pending, use only its stage/run/digest with resume=true. Never republish.
If reply arrives immediately, retain that result; do not restart to force pending.
Compare immutable request hash/mtime before and after resume; verify one action,
one compiled program, neutral verified release, saved geometry and terminal
owner/cleanup. Preserve failures; no sensors/helpers/Docker restart.
This tests real asynchronous reply collection, not crash recovery, live games,
latency improvement, token savings or arbitrary concurrent controllers.
