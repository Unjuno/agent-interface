# R08 deterministic callback drain correction

R06 and R07 remain separate failed design attempts. R08 incorporates only the specific evidence-backed test corrections: allow up to 20 seconds for the worker-start gate, and obtain `call_id` from the outer exact-result envelope (the raw observation report intentionally omits it). There is no `interface_close` on this one-shot server, so teardown follows completion of the callback Future and exact report readback.

Run one normal and one `-O` process. The synthetic observer blocks past the unchanged 8-second caller timeout, then is released once. The test verifies exact-call identity, finalized report/no temp file, one invocation, and no input or replay. No retries or replacements. This remains a test-harness lifetime check only.
