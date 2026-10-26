# S43 custody assessment

The original preregistration, runtime result, forced-poll trace, runner sources, Xvfb logs, cleanup receipt, and hashes are retained. An independent audit was rerun from the copied raw result and passed 28/28 checks. Newline-normalized source bytes match the four Git blobs at both execution commit `c058acb` and current main `949fd12`.

The trial's scientific classification remains `PASS_SCOPED`; evidence completeness is partial:

- `raw/original/raw-harness-output.jsonl` is zero bytes, so the host-side SDK invocation was not captured there.
- The packet does not retain hashes/manifests for the external Python stage, dependency bundle, or XKB data. The audit therefore does not establish their exact identity or full replayability.
- The compiled host harness is omitted from the public packet because its embedded PDB metadata contains a local user path. The C# source and project file are retained. The original local packet remains unchanged.

The retained WSLc VHDX is 236,978,176 bytes with SHA-256 `d23c5987eecdfca7306a091f93a90ae0b30e975f17ab995ddbb9fec55e6fc25a`; it is not included in this public packet. Host-specific paths in JSON are redacted and their original/published hashes are recorded in `REDACTIONS.json`. `raw/RAW-SHA256.json` retains the original raw receipt hashes; `PUBLIC-RAW-SHA256.json` records hashes of the published redacted files.

No global WSLc inventory or Docker operation occurred in S43. Its unique session/container cleanup passed; this result does not inspect or change other sessions.
