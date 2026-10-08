# Idle managed lifecycle follow-ups

Two distinct private WSL/Xvfb Calc cases extend the owner-lifetime construction
in ../native-owner-lifetime-01. Both use real native MCP, the managed allocation
and Calc harness; neither submits input. They are integration checks, not the
frozen #4124 formal matrix, a matched performance study or task completion.

- Server termination: source edbb9c56b6d417705eb37bc5d03facd16743f628,
  seed 991319. The probe obtained the actual owner's parent identity and used
  pidfd_send_signal(SIGKILL) for that MCP server. The invocation returned without
  exception; no server wait status is retained. The harness took the EOF failure
  path, existing cleanup completed, external waitpid reaped exit 1, and tracked
  process PIDs were absent. No external rescue or task evaluation occurred.
- Explicit stop: source 9e03ad63d (full ID in PLAN.json), seed 991320. The primary
  started Calc, called native_stop, polled native_status to terminal exit 1, and
  repeated stop/start on the same connection. The same PID stayed terminal; no
  process was relaunched. A subsequent tool listing succeeded on that connection.
  Tracked PIDs and owner were absent after cleanup, with no input/task evaluation.

Plans, drivers, RPCs, initial PNGs, error/cleanup records, audits and original
inner manifests are retained unchanged. RuntimeError/exit 1 is preserved as
owner-lifetime termination, not relabeled task success. Cleanup flags for owner
and arbitrary descendants remain unverified in the harness receipt; external
observations are separate. No instantaneous cancellation, active input release,
killed-worker recovery, arbitrary descendants, model usage, throughput or latency
benefit is established. Timings after context close are not signal-to-release
measurements. Subreaper use belongs only to the server-kill probe's collection.

Run python3 runtime/results/native-cooperative-stop-01/verify.py. This standalone
standard-library verifier reads the archive in memory, checks both manifests and
record consistency, and never extracts or executes archived files. It does not
independently re-observe processes, judge pixels or attest the runtime environment.
