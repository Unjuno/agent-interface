# Construction chronology

- First zero-training Docker preflight stopped at exact runner Git-blob verification because local materialization had an extra terminal blank line. No model updates occurred.
- Corrected materialization; local Git blob then matched public main runner ecd3a0414178f38535406573314793a40b353878 exactly.
- Offline pinned Docker construction passed sentinel-byte, exact 64→16 prefix, corrupted-prefix rejection and source parse checks; zero optimizer updates.
- Initial candidate seed 7866301/v3 was abandoned before source upload or run when a concurrent exact branch appeared; it remains untouched. Seed 7866401/v4 is the sole allocation for this diagnostic.
