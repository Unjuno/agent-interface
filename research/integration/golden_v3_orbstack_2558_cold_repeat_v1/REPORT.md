# #2558 cold/second-call fresh keyboard-contract allocations

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: after a fresh fixture observation, a repeated model call can preserve the keyboard contract and still pass native admission/effect gates; this may indicate a repeat-call timing difference, but it is not automatically a persistent-session warm result.
- T: run three fresh OrbStack fixtures. For each, perform two host-local Codex calls against the same fresh observation using `compiled-form-grounding-keyboard-v1`; use the second plan for native handle action, independent effect, release, continuation, and focus-change guard.
- D: 3/3 effects succeeded; 3/3 visual revalidation; 3/3 releases; 3/3 guard refusals with zero emissions. Cold model wall mean 12,342.976ms; second-call mean 11,170.050ms. Cold mean input 16,092.7 with 5,034.7 cached; second mean input 15,250.3 with zero cached. Action-to-scored-effect values were 147.559, 146.174, and 154.474ms.
- C: `PASS_THREE_FRESH_COLD_REPEAT_SCOPED`. The second call was a separate ephemeral Codex process, not a persistent model thread; no warm-cache or persistent-session claim is made.
- U: wire the keyboard contract into the actual persistent golden runner and repeat cold/warm/invalidation/repair with the preregistered session semantics.

## OrbStack provenance

- Docker context: `orbstack`
- Image: `agent-interface-2558-orbstack@sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398`
- Docker Server: 29.4.0
- Three fresh private Xvfb/fixture processes.

Previous results remain immutable; this is additive evidence.