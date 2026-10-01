# Completed recovery response through MCP

Source under test: 53ee3efed. This check attaches the actual MCP stdio server to
the completed local native-target-recovery-01 run and calls native_resume by the
exact committed SHA256 for stages 1 and 2. It does not launch a GUI allocation,
submit input, or ask a model to decide. The output path must be outside the run.

The earlier refusal returns its same retained image and reports already_submitted
because stage 2 is now occupied. It retains the refusal summary instead of
claiming an action completed. Stage 2 returns the successful terminal receipt
with continuation unavailable. Both returned image hashes match their recorded
references. All 40 retained run files have identical hashes and mtimes before and
after the calls. report.json includes the snapshots and returned metadata; image
bytes remain in the existing frozen live trial. This is read-only integration
coverage, not another live recovery success or a latency benchmark.

Run with the MCP environment and PYTHONPATH=.:research/live_control:

    python research/live_control/native_recovery_resume_v1/check.py --run-directory /explicit/completed/run --output /outside/run/new-report.json

The output is created exclusively. The original absolute source/image paths must
remain readable; an archived copy at a new path requires separate relocation
handling rather than rewriting the frozen original evidence.
