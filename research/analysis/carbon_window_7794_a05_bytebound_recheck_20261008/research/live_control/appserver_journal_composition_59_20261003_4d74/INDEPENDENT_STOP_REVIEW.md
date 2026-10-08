# Independent saved-data STOP review

Reviewer: /root/a05_science_audit, read-only, no client/producer/auditor execution.

All6 unique expected cells STOPped with peer file readiness deadline exceeded, before any caller/checkpoint/holder timestamp. Peer-ready events exist only for main healthy, main held, bounded held:405.411/474.595/478.072ms after client_constructed and25.303/117.412/104.311ms after cell_stop. Other3 peers lack ready records and were SIGTERM-reaped around562–565ms after construction. Missing peer_received files must not be counted as measured zero bytes.

All6 journal and peer/worker stderr/stdout files are actually0 bytes. Each peer was reaped, all3pipes andjournal closed, allreader/caller/holder endpointsfalse, no cleanup/thread errors. Threepeers exit0 viaEOF, threeexit-15 viaSIGTERM; allworkers exit2, no watchdog fired, group absent in all6 stop cleanups. stderr contains swap-limit/cgroup warning only. No CPU or mount-latency instrumentation exists, so causal attribution remains unresolved.

A separate startup-only control can qualify2s readiness/6s containment while preserving A01 STOP and exact50/250/400ms/client variants. No scientific outcome is supported by A01.
