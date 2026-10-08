# #1490 self-action publication freshness fence

Role-demotion successor to immutable #475/#498 and correction #509 under #701.

H: a relevant self-action receipt should invalidate prior target evidence only until a fresh publication explicitly covers that action sequence. It is negative evidence during the publication gap, not persistent semantic identity.

T: standard-library deterministic state machine + independently structured event-history oracle. Directed construction, source freeze/readback, then one 240,000-history formal invocation at seed 149020260918001. No Inkscape/X11/model/provider/network/task input.

D: stale publication-gap effects0; stale-covered evidence effects0; fresh-negative effects0; fresh-positive effects40000; irrelevant-action false rejection0; authority/cross-scope/future/duplicate controls fail closed; VISUAL_ONLY exposes stale effects; ALWAYS_HISTORY exposes fresh-positive overinvalidation; independent audit/corruption controls pass.

C: external/unreceipted mutations remain invisible to this mechanism. Production may use a broader observation/currentness generation rather than a dedicated self-action sequence.

U: synthetic lineage semantics only; no GUI timing, paint-lag frequency, model/token/task/runtime promotion claim.
