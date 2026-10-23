# R29 preparation and custody

The WSLc host state was checked against the latest #7924 record: the pinned image was not cached in the latest bounded attempt, no full CID was recorded, and cleanup/owner state remains unresolved. WSLc was not started, listed, pulled, built, or cleaned. This fresh attempt used the user-authorized PC's owned Win32 fixture, which directly exercises the unresolved native input-release boundary.

Before the one-shot trial, an input-free preflight passed: current-main commit and tracked tree, R14 raw/audit hashes plus the 19/20 blocked-hook semantics, R15 no-dispatch prelaunch refusal hash, current runtime and packet-script hashes, read-only `LowLevelHooksTimeout` absence, native Windows, and compilation. A process query found no existing Python fixture or stdio-MCP server. The conditions file itself was not independently hashed in that preflight receipt; final custody SHA-256 covers it and the raw embeds the resulting attempt/program/sentinel and timestamps. This is recorded as an integrity limitation.

One fixture, one dispatch, one cancel, and exact-call polling were used. The hook callback was released at the planned bounded hold; no replay, retry, extra cancel, registry mutation, WSLc, or Docker operation occurred. Every exit and foreground restoration was checked.
