# Fail-closed handling of unknown job-class metadata

- **Status:** Scoped finite boundary result merged; no scheduler claim.
- **Source:** Issue [#8061](https://github.com/Unjuno/agent-interface/issues/8061), successor to [#7748](https://github.com/Unjuno/agent-interface/issues/7748).
- **Idea:** Verify that missing, malformed, or unrecognized job classes produce a typed hold/unknown outcome before control-only demand can be silently omitted.
- **Outcome:** Merged [PR #8070](https://github.com/Unjuno/agent-interface/pull/8070) preserves the finite boundary result and a distinct OrbStack preflight stop. It does not demonstrate OS scheduling, runtime control, GUI behavior, or physical release.
