# Methods history (excluded from native allocation)

Before implementation, source extraction and verdict tests failed with two
NotImplementedError exceptions (RED); after implementation both passed.
Expanded saved-auditor wrong-source test initially failed because matching
wrong source receipts were accepted (RED). Auditor now pins source SHA256,
and rejects duplicate JSON keys and wrong emitter payloads. Five unittest
methods cover source identity/rejection, original functions on saved lines,
typed custody gates, saved audit positive and four semantic mutations.
An additional sixth test confirms three injected pipe-close errors do not skip
wait, reader join, stderr read or subsequent closure attempts. The earlier shape
mutation was strengthened to update summary and row consistently. Five semantic
mutations now reject custody, boolean/shape substitutions. These are construction
checks, not native runs, not full audit mutation coverage. Independent reviewer
Singer's initial HOLD caused guarded startup, error-retaining cleanup, producer
PPID/AST binding, successful emitter byte count and strict bool improvements.
