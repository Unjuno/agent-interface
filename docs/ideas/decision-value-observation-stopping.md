# Decision-value stopping for adaptive observations

- **Status:** Historical A01/A02 evidence remains distinct; later launcher STOP is noncanonical.
- **Source:** Issue [#7934](https://github.com/Unjuno/agent-interface/issues/7934).
- **Idea:** Select the next observation or verification action by its marginal expected value to a downstream decision, rather than information gain alone.
- **Outcome:** A01 `FAIL_AUDIT` and separate A02 `PASS_CALIBRATION_BOUNDARY` are preserved in merged [PR #7948](https://github.com/Unjuno/agent-interface/pull/7948). A later launch attempt stopped on an output-path issue and is explicitly noncanonical; it does not revise historical results. Successor [#7955](https://github.com/Unjuno/agent-interface/issues/7955) tests likelihood ambiguity sets as a distinct finite question. No runtime policy or safety relaxation is established.
