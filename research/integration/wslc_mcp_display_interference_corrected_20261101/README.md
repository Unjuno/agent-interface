# Corrected-fixture MCP display-interference comparison

This candidate preserves two previously run single allocations, not new runs.
Each uses two in-process MCP server objects and distinct real guarded child
processes with an idempotent fixture that logs one delayed `b` injection per
owner. In r168 both owners use one synthetic target on one private Xvfb; in
r169 the harness provides two Xvfb displays and two synthetic targets. The
fixture clears the first `a` hold, the second owner holds `a`, and then the
first is cancelled before the second. The second hold was up after the first
cancellation in r168 and remained down in r169. Both old actions and closes
were UNKNOWN and replay was forbidden.

The comparison varies both the display and target and consists of two
fixed-order, forced-interleaving trials, not a randomized reliability or speed
measurement. The target in r169 saw six press/release pairs during one extended
hold; autorepeat was not controlled in that allocation. No old-task success,
general queue drainage, MCP transport isolation, integrated display ownership,
physical-desktop behavior or MAP01 result is established.

Both per-allocation manifests and local raw remain unchanged. The historical
audits in each trial directory run in this layout; r168 uses the retained r150
manifest as its source-comparison baseline. Local-path `private-command.json`
records are intentionally omitted; no ephemeral display authority is included.
The two source trees are kept verbatim because the per-run manifests bind their
exact paths and content. See each `RESULTS.md` and `conditions.json` for scope.
`python -B verify_raw.py` also compares summary entries against the separate
target event and injection log files. Keymap observations remain in the trial
result JSON and are not independently reconstructed by that check.

The recorded evidence is separate from the unmerged runtime prototypes and is
not a recommendation to treat either recovery implementation as complete.
