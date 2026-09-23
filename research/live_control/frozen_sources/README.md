# Hash-addressed execution sources

These files preserve exact source bytes used by retained runs when a historical
revision name collided with an existing source file. A result plan still records
the original execution-time path and hash. Audits may use the directory named by
that hash after first confirming that the current path no longer matches.

The first entry preserves the delayed-hover implementation that temporarily
occupied `session_v10.py` during OpenTTD TimingEnvelope runs 03–08. The preexisting
drag-checkpoint `session_v10.py` was restored. A second collision with the
existing `session_v11.py` was caught before further execution; the current
delayed-hover candidate continues as the next unused revision, `session_v22.py`.
