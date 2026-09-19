# Clock identity and explicit missing intervals

Issue #46 requires a timing envelope that separates clock domains and missing
endpoints. timing_clock.py adds a Linux-only clock descriptor: perf_counter's
reported implementation/properties, boot ID, time namespace identity and namespace
offsets. Its domain ID hashes the domain fields. Unsupported implementations or
unavailable proc metadata produce unavailable/null identity, never an invented
epoch or offset.

Python documents perf_counter as a shared process clock with an unspecified
reference point, and exposes its implementation and resolution through
[get_clock_info](https://docs.python.org/3/library/time.html#time.get_clock_info).
Linux [time namespaces](https://man7.org/linux/man-pages/man7/time_namespaces.7.html)
can virtualize monotonic clocks with namespace offsets. Recording only the name
perf_counter_ns is therefore insufficient for comparing arbitrary environments.
This candidate conservatively requires matching boot, namespace, offsets and
implementation before subtracting cross-process timestamps.

interval returns no duration for absent timestamps, missing clock identity,
different domains or reversed ordering. Matching clock metadata does not establish
that endpoints mean the same thing, prove causality, or measure scheduling error.
The descriptor explicitly leaves endpoint uncertainty unmeasured; resolution is
not a claimed bound on measurement accuracy. It does not synchronize clocks.

Candidate interactive_v28 writes timing-clock.json once at startup and attaches
its domain ID to emitted raw events. Socket v12 launches this runtime. Candidate
prepared_exchange_v5 records its own descriptor alongside client timestamps.
No clock-file read is added inside input release or cancellation callbacks; event
serialization does grow, and its performance overhead is not yet characterized.
Admission and lease logic are unchanged; clock identity grants no authority.

Two live Linux processes reported the same domain and ordered parent/child
timestamps. Four controls return null duration for missing timestamp, missing
clock, changed domain and reverse ordering. A full scripted Calc gate test then
verified runtime/entry-client/confirmation-client descriptor equality and the
domain ID on every raw runtime event. Client send-start to runtime command receipt
was 871486 ns in that one sample. A missing model start remains missing_endpoint
with duration=null. Twelve exact frames, saved workbook/hash, release, request
lineage, full prefix and early-return/final-continuation checks still pass.

This is only a first part of Issue #46. It does not supply model receive/generation
timestamps, per-endpoint uncertainty, CPU/queue attribution, an OpenTTD comparison,
matched ordering/model/output limits or instrumentation-overhead measurements.
No extrapolation to human tempo or cross-OS clock mapping is valid. A process
changing its time namespace after startup would invalidate the cached descriptor;
the current fixture does not do so. The descriptor is local metadata, not an
authenticated clock attestation. Historical records lacking it remain unlabeled.

Evidence: results/timing-clock-01 and results/timing-clock-live-01. Source manifests
include runtime, clock helper, client and scripted gate wrappers. Older measured
versions remain unchanged. Next attach these identities to a consistent set of
client endpoints and measure serialization/critical-path overhead before adopting
the instrumentation across benchmark domains.
