# A11 publication note

The public runner and auditor differ from the executed copies only in host mount-root handling: they derive the outer checkout from the nested source worktree and validate mapping structurally instead of embedding a machine-specific absolute path. The exact executed hashes are preserved in local `FREEZE.json`. Raw audit JSON with transient intent tokens and per-key identities stays local. Public audit files are aggregate projections keyed to the original raw audit SHA, not copies of the raw audit.
