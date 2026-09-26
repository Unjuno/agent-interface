# Construction 02 — full v3 matrix (not v4 formal evidence)

The v4 construction entrypoint reused from v3 has no cell selector. It ran the complete 14-cell v3 matrix, rather than the two cleanup-failure cells declared in the draft v4 CASES.json. This output is retained unchanged, marked construction-only, and excluded from all v4 outcome scoring. No v4 formal command has run.

The row identities and container raw are preserved in `CONSTRUCTION.json` and `CONTAINER.json`; source/image/command facts are recorded alongside them. This exposed a runner/plan mismatch. Formal execution is held until the runner supports exactly the declared two cells and construction confirms that bounded invocation.
