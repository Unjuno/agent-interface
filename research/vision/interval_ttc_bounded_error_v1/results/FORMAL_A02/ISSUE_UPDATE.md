### A02 one-shot formal disposition

- Candidate: 1 invocation, exit 0; 200 sequences and 2,400 prefix estimates.
- Independent auditor: 1 invocation, exit 2; 98 reconstruction mismatches, all in the occlusion profile.
- Preregistered disposition: `FAIL_METHOD` on the integrity gate. Scientific comparison is unscorable because the auditor checked later missing observations before reconstructing earlier prefixes.
- The first raw candidate output and auditor report are preserved. No candidate or auditor retries were made.

The full frozen protocol, hashes, raw outputs, report, and diagnosis are in draft PR [#8194](https://github.com/Unjuno/agent-interface/pull/8194). Execution was synthetic-only in a network-disabled pinned OrbStack container on macOS; no GUI, model, game, input, or runtime integration was used.
