# Compositional gain margins for coupled visual-control loops

- **Status:** Finite method result passed; applicability to real GUI loops remains unverified.
- **Source:** Issue [#8470](https://github.com/Unjuno/agent-interface/issues/8470), successor to [#6195](https://github.com/Unjuno/agent-interface/issues/6195).
- **Idea:** Test a compositional gain screen for coupled local loops with delay, disturbance, estimator, and release effects, keeping component-level checks separate from whole-loop composition.
- **Outcome:** T0 `PASS_METHOD_SCOPED` on eight finite exact-rational cases. The independent audit reconstructed 8/8 rows and rejected 3/3 mutations. One coupled case exceeded the feature bound although all isolated component checks passed; other cases demonstrate conservative refusal. The work does not certify a live GUI loop, runtime, or safety. Merged [PR #8479](https://github.com/Unjuno/agent-interface/pull/8479) contains the frozen package.
