# Ordinary admission owner-instance alias — construction result

Decision: `PASS_ORDINARY_ADMISSION_OWNER_ALIAS_SCOPED`.

Pinned source identity: current `research/live_control/input_owner_v10.py` Git blob `341b3c01649943ddaad5f28431a792c4889cc36e` at BASE `8888ce1b5642932c00c40668c557ff8341b93555`.

Current v10 creates an owner-lifetime identity (`self.owner_id`) and exposes it in `input_state` and continuation-related paths, but an ordinary keyboard `input_admission` contains only `event`, `key`, `admitted_ns`, `input_ack_ns`, and `valid_until_ns`.

A standard-library information-flow construction compared 100,000 matched owner-A/owner-B pairs. Hidden owner IDs differed in every pair while key, admission/ack clocks, and lease deadline were held equal. Complete public admission dictionaries were identical 100,000/100,000; public mismatches were zero. Ten fixed controls passed, including checks that public key/timing/deadline changes remain visible and malformed harness inputs fail closed.

This is a receipt-sufficiency result, not evidence that owner lineage is unavailable to the surrounding caller. A trusted adapter can bind owner identity out of band. The narrow conclusion is that the ordinary admission receipt alone is not a sufficient owner-lifetime provenance key for later physical-edge/actuation composition.

Construction seed `100720260917001`; digest `768356d23b9084aeb8a86460729bc41913c1e8ab324d1ec6a878aad46f84ec3e`; Python 3.13.5. No formal/live allocation and no task input.
