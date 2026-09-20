# Primary public MCP continuation in WSL

Source: `25bb8a6472cccc03cdaaa2fffeb214339bc35e62`. One owned Xvfb/Tk session, public MCP via the Python SDK and shell, not a registered desktop-host tool. This is a scoped functional-use record, not formal container acceptance or a performance comparison.

The primary assistant viewed the initial empty entry, then chose to enter `482` with explicit `gap_ms: 20`, save with Ctrl+s, capture with zero final delay, and release input. The harness supplied the 10-second lease immediately before dispatch; source sequence 1 and binding revision 0 were caller supplied. The saved effect contained `482`, execution completed and release was verified, but the returned image showed `48` and `unsaved`.

Reading the retained result returned exactly the original image and outcome without changing the existing request/report/image files. After viewing that image and the independent effect, the primary chose one new read-only observation, which showed `482` and `saved:482`. Input was not replayed. There were two observe calls, one dispatch call and one retained-result lookup.

Decision: retain the existing distinction between result lookup and new observation. A completed action does not imply its image represents the application after redraw. This one result does not justify a universal delay, automatic re-observation, or a new default text gap.

The archive contains raw requests/responses, original PNGs, effect and event files, the exact local harness scripts and decision, primary interpretation, cleanup receipts, and a SHA-256 manifest for 35 files. `archive.json` identifies the archive digest. The owner exited 0; the tracked Tk child was terminated/reaped (-15) and Xvfb reaped (0). Descendant absence was not independently verified. All owned work was terminal before archiving.

No latency comparison, host presentation acknowledgement, token/cost measurement, broad GUI claim, or formal #3352 acceptance is made. The time between calls includes primary tool/turn delay. Historical evidence remains unchanged. Collection scripts are evidence, not commands to rerun a frozen allocation.
