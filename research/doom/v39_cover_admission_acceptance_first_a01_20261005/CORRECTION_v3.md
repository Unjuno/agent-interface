# Candidate v3 context correction

Candidate v3 exercised the accept-first order and proved that the extracted wait returned before seeing the hard event. Its extracted test closure began with `latest = None`, whereas the production controller enters cover submission with a previously accepted observation in `latest`. The v3 candidate therefore cannot substantiate reaching planner input preparation on the production path. Preserve v3 files and outputs as the ordering-only result.

Candidate v4 seeds the exact wait closure with a neutral prior observation before `accepted`, verifies that prior observation is current at acceptance return, and then verifies that the hard observation remains unseen until the next monitored wait. This repairs the source-context limitation without changing the frozen hard-event/acceptance ordering hypothesis.
