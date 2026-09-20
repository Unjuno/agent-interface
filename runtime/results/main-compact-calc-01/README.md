# Main compact-receipt Calc self-use

One primary-agent WSL/Xvfb use of main `b732fa5c3d4c828ea50f81c36522a61e7803e473`, using the packaged public MCP server and `compact=true, report_refs=true` on every call. The primary inspected saved PNGs between decisions. This is SDK-mediated primary use, not direct registered-host tool delivery or a formal container experiment.

The primary closed the visible startup tip, entered Quantity / Unit price / Total and values 8 / 17 with formula `=B2*A2`, then saved. The final screenshot and saved FODS both show 136. Two dispatches completed with verified input release; two explicit observations were used. The entry/save response image was intermediate/saving despite completed execution, so the primary explicitly observed again before declaring completion. There was no action replay.

## Evidence and reproduction

`evidence.tar.gz` preserves 54 local files, including raw requests/reports, model-visible text/image responses, screenshots, exact runtime archive/manifest, initial and saved documents, task, decisions, owner harness and cleanup. `manifest.json` identifies every archive member. `archive.json` binds the archive bytes. The original local evidence manifest is retained inside the archive.

Run `python verify.py` from this directory (standard library only). The verifier reads the archive without extracting or executing its harness/runtime, verifies exact bytes, checks response/image/source consistency, counts calls, independently reads the saved formula/value, and inspects recorded cleanup. To inspect images, extract into a separate empty directory and compare `action-2.png` with `action-3.png`. Do not rerun `run.py`: it records a historical allocation, fixed display/profile and one-shot guard.

## Findings and limits

The last fixed wait requested 50 ms and lasted about 50.13 ms. Total requested waits were 570 ms, including character gaps; runtime execution was about 645.40 ms. SDK roundtrips were 250.50 / 174.52 / 732.59 / 106.92 ms. These exclude primary reasoning, orchestration and host image presentation; they are not useful-feedback/human-speed measurements and have no matched baseline. Token/cost usage was not measured.

The owner exited 0. Calc launcher, Openbox and Xvfb were reaped with 255/0/0; all captured process-group member paths were absent. Full descendant closure remains unverified. The archived document lock file reflects this termination path; it is not proof of an application-level graceful close.

This evidence supports this one task through the integrated response format. It does not establish general GUI performance, a default delay change, container acceptance or broader model usability. The follow-up comparison is [#3700](https://github.com/Unjuno/agent-interface/issues/3700). Preserve earlier runs unchanged.
