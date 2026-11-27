# R29 result — stopped before MCP

**Disposition: `STOP_HARNESS_TITLE_MISMATCH_BEFORE_MCP`.** This is not a pass
or failure of the runtime recovery path; the public path was never entered.

The frozen attempt used one fresh R29 fixture. Computer Use selected and raised
the unique R29 window. The independent probe read the exact expected HWND
`11014098` and PID `26604`, but returned `foreground_matches=false` because the
reused R24 helper also required the literal title `Agent Interface Win32
Fixture R24`. The observed title was `Agent Interface Win32 Fixture R29`.
This was confirmed in the copied helper source and retained probe output.

The stop condition was honored: zero public observations, zero public
dispatches, zero recovery calls, and zero task verifications. The fixture was
closed; the durable custody fence remained clear. No task effect, input release,
recovery, efficiency, MAP01, preview, or reliability result is claimed.

The frozen IDs and conditions remain unchanged. This consumed R29 as a harness
preflight stop. A corrected condition-driven title probe requires a new
allocation ID; R29 must not be rerun.

Raw probe, fixture metadata, foreground selection record, stop boundary, and
fence snapshot are preserved under `raw/`. The top-level SHA-256 manifest is
regenerated after this disposition.
