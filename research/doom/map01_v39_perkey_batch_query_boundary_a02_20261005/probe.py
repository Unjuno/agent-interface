#!/usr/bin/env python3
"""Fail-closed entry point for the already-consumed A02 candidate."""
raise SystemExit(
    "A02 is consumed. The original candidate is archived at "
    "results/a02/archived_candidate_probe.py; do not execute it. "
    "Use the read-only audit commands in COMMANDS.txt."
)
