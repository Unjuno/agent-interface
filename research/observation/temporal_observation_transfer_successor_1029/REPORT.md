# Issue #2013 successor — bounded temporal observation transfer

## H/T/D/C/U

- **H:** A bounded temporal observation ring transfers source, timestamp, and scope provenance to a controlled live-like capture fixture without treating dropped intervals as unchanged.
- **T:** Use monotonic fixture timestamps, a known visual transition, an action-adjacent sequence gap, one ROI, two surface identities, and expired history. Compare current and historical roles.
- **D:** `experiment.py`, four captures, sequence/timestamp/scope ledger, drop interval, ROI digest, and stale-query result.
- **C:** Current/history roles remain distinct; dropped interval is reported; scope B is excluded from A; ROI bytes are exact; expired history returns no current evidence.
- **U:** Real GUI cadence, capture latency, model benefit, token cost, and runtime promotion remain unknown.
- **STOP:** One controlled fixture run; no live input, model, network, or user data.

## Result

Command: `python experiment.py`

- 4 captures across scopes A/B.
- Scope A query returns current sequence 3 and historical sequences 0,1.
- Missing sequence 2 is reported as drop interval `(1,3)`, never as unchanged.
- ROI extraction exactly recovers the changed pixel; ROI SHA-256 is `a810ae6aa1940d0b663bb31cd466142ebbdbd5187131b92d93818987832eb89`.
- Expired query returns no current evidence.

**Decision: PASS_TEMPORAL_OBSERVATION_TRANSFER_FIXTURE_SCOPED.**

This is a controlled ledger transfer result, not evidence of real GUI cadence, model benefit, latency/token savings, or runtime promotion.
