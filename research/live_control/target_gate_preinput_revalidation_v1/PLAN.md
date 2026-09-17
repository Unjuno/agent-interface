# Target-gate pre-input revalidation v1

Task: TARGET-GATE-PREINPUT-REVALIDATION-20260917-001
Issue: #979
Publication base: 6e7d7168a87e4de888ae5b9488f9ec53a2cb54af
Predecessor: #965 PASS_TARGET_GATE_TOCTOU_EXPOSED_SCOPED
Exact inherited app Git blob: 5710e0fabffafae04e5599ce77e3154423da6ec6

H: Re-evaluating the exact same 11x11/radius5/max-RGB-error<=8 visual-currentness predicate immediately before pointer input will preserve stable liveness while refusing the #965 visually-changing post-gate swap before input.

T: Private Xvfb/Tk cases. SINGLE_GATE is #965 one-gate behavior. PREINPUT_REVALIDATE adds exactly one fresh screenshot after the same optional swap point, at the same A coordinate and threshold. It rejects TARGET_EVIDENCE_CHANGED without input when the patch no longer matches. No target search, relocation, semantic role input, model, network, or shared runtime mutation. Formal = 4 reps x stable/swap x two policies =16 sessions, one block invocation, reruns0.

D: PASS only if first gate eligible16/16; stable clicks task-target under both policies4/4 each; swap+single clicks decoy4/4; swap+revalidate captures strictly after mutation, rejects4/4 and clicks0/4; all terminal button states neutral; source/audit integrity passes. HOLD if the mutation no longer changes the frozen patch. Candidate click after rejected second gate is FAIL_REVALIDATION_ESCAPE.

C: This only addresses visually changing TOCTOU. It cannot solve #956 pixel-identical semantic aliases, and a residual race remains between the second capture and actual OS input.

U: Synthetic Tk/X11 fixture; no natural mutation-rate, semantic identity, model/token, cross-backend, production-security, or atomic-transaction claim.
