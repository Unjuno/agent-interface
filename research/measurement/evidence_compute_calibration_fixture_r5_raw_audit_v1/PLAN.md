# #1765 Independent raw audit of #1737 calibration fixture

H: the exact #1737 first RAW can support scoped calibration interpretation only if an independent auditor reconstructs every row cost from primitive completion_wall_ns + obsolete_cpu_ns, verifies independent job digests/schedule/cache semantics, and never trusts #1737 RESULT aggregates.
T: retained-data only; pinned RAW sha256 71e9a44f...; frozen schedule sha256 25fdc3ed...; independently reimplemented 8MiB/64KiB/4-round digest oracle; exact row-cost reconstruction; seven corruption/independence controls; one formal audit invocation after source freeze; no job execution.
D: 128 rows/64 pairs/48+16 mix; row-cost mismatch0; digest128/128; stale0; invalidated RUN abort+obsolete16/16; p=1/4; g,w means>2ms; p*>1/4 and direct RUN aggregate lower with exact identity; cache48/8/8; version summary structurally valid; corruptions all rejected; predecessor RESULT mutation scientifically irrelevant; formal1/reruns0.
C: salvages interpretation of one frozen raw allocation only; does not repair #1737 auditor or make authored p/reuse deployment estimates; utility and host timing remain fixture-specific.
U: raw-evidence audit only; no allocation rerun, GUI/model/token/production claim.
