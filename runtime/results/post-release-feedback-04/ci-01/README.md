# Hosted CI fixture-clock correction

The first hosted native-mcp checks for head 0e371aea146e7ff4aaedb5a4cd1a6523cc01541f failed the new no-inline summary test. The fixture retained execution/wait timestamps from a host with ~989 seconds uptime, but release/end/capture used the new runner's current clock. A fresh host with 20 seconds uptime therefore produced ended_ns < started_ns. Full fallback was the correct runtime response to that invalid report.

reproduce.py retains the short-uptime reproduction and exact failure, without GUI input. The added fresh-host regression subcase failed before correction. The test now translates only its historical mocked execution/wait timestamps into the same current clock domain as release/capture, preserving their relative interval. The short-uptime subcase and 18 post-capture/summary tests pass, followed by the shared 335 protocol and 141 harness checks. Production clock validation and summary fallback are unchanged.

The live six-task source remains 3161424cc; this test-fixture correction does not rewrite or rerun either frozen arm. original-hosted-failure.log.gz preserves the first remote failure; result.json and compressed suite logs retain the new local checks. These are construction/CI records, not new formal GUI evidence.
