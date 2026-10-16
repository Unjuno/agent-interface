# Measured caller persistence cost on a fixed GUI observation workload

Three new measurement drivers use the frozen received_exchange_v2 API and durable_submit_v3 candidate. No caller/transport implementation changed and no default was promoted. Measurements retain all runs and have no model calls. The task is repeated clockÅ®observe-only submit on actual Inkscape seed236, not the full rectangle-edit benchmark. Independent SVG checks confirm no changes and are not scored as edit task success.

## Actual GUI API comparison

results/caller-cost-01 uses ABBA received/durable/durable/received with four fresh GUI sessions, four clock/observe cycles each. Each session has eight measured API calls,36 runtime events,five exactly reconstructed frames and four completed/released observation programs. Initial capture, runtime startup, journal initialization, finish and result logging are outside the timers. The transport callback is timed within the outer API timer; outside-transport residual includes validation, copying, locking, JSON, filesystem operations and bookkeeping. It is not a direct fsync measurement. Both paths use equal-length unique IDs; baseline generates IDs before its API timer, durable generates them inside. This small identity-generation asymmetry remains a limitation. The baseline is the in-memory request_once API, not its CLI that writes evidence files. The two APIs provide different crash-persistence guarantees.

Per-operation medians,8 samples each:

| API | operation | total ms | outside transport ms |
|---|---|---:|---:|
| received | clock |22.259|0.165|
| received | observe submit |94.168|0.255|
| durable | clock |51.035|33.605|
| durable | observe submit |116.239|35.812|

Eight-call session totals: received473.645/453.091ms; durable690.722/678.026ms. Transport time also varied, so subtracting session totals does not isolate persistence cost. This identifies a material caller-side overhead in this setting, not a universal regression estimate. Images for repeated static observations were reused; no pointer/input movement, dynamic visual workload, long journal or model interpretation is covered. The runtime image-ready timestamps are reported separately in timings.json; they do not establish when a model received or understood an image.

## Same durable API, different journal location

results/journal-location-01 uses ABBA mounted/native/native/mounted, the same four-cycle GUI task and durable_submit_v3 throughout. The audit checks the recorded actual journal paths; native temporary journals are on /tmp and copied to evidence only after timing. The plan's inherited environment journal_filesystem string describes the repository filesystem and is not correct for the native arm: journal-location.json per session and filesystems.txt are authoritative for actual location. findmnt confirms /tmp is on ext4 and /mnt/c uses9p/DrvFS. Neither temporary test directory is a production restart-storage policy.

| location | operation | total median ms | outside transport median ms |
|---|---|---:|---:|
| mounted | clock |52.714|33.602|
| mounted | observe submit |117.949|35.089|
| native | clock |50.375|31.246|
| native | observe submit |113.490|31.204|

Native session totals655.545/703.095ms overlap mounted690.538/663.397ms; native also has a77.475ms clock outlier. Native placement alone does not remove the overhead or establish a consistent end-to-end gain in this small sample. Do not adopt location-only optimization based on its better medians. Audit verifies64 measured API calls across both studies, eight clean runtime exits, every event slice/received continuation, clock/sequence/deadline association,40 exact frames and unchanged SVGs. Each study uses only two sessions per condition; samples within a session are related, no confidence interval or broad causal claim is made.

## Static store profiling narrows the next change

results/journal-store-profile-01 profiles8 calls to unchanged store per arm, mounted/native/native/mounted, using a fixed captured journal. This is cProfile with profiling overhead, outside GUI execution; it cannot be numerically substituted for the earlier live residual. Native8-store wall123.907/127.460ms includes posix.fsync113.655/117.026ms, about92% of measured store time. Mounted8-store wall197.239/229.726ms spreads time over fsync,replace,open,unlink and other filesystem calls. JSON is not the dominant native cost in this profile. The store creates and fsyncs a new file, replaces the checkpoint and fsyncs its directory on each pre-send and post-reply commit.

Next investigate a bounded append journal or equivalent storage layout that reduces repeated directory updates while preserving pre-send durable uncertainty, atomic received state and cooperating-process exclusion. Pin recovery invariants and test truncated/failed appends and actual process-loss recovery before measuring any speed improvement. Do not simply remove fsync or batch input requests across uncertain outcomes. Use the resulting caller in an actual model-facing loop; token cost, model waiting and human-like interaction speed remain unproven.
