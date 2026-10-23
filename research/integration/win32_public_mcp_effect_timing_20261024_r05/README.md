# Public Win32 full-client visual response R05

## Question and scope

Can the standard public stdio-MCP path produce an independently verified task effect and a retained post-action capture that shows the complete short sentinel in the Win32 fixture? R03's final image confirmed a visible response but clipped the text tail at 300 px. R04 failed before input because 420 px was the outer-window width and exceeded the actual client bounds. R05 reads the owned HWND's `GetClientRect` and uses the exact measured width and height for both public observation calls. The unique visible task is `VISUAL-R05`.

The probe forwards the matching target generation from the immediately preceding observation, uses one finite click/text/save/release dispatch, records timing with `perf_counter_ns`, reads the independent effect file and event journal, and closes only its owned fixture. It does not retry. The task sentinel is intentionally short so it fits beside the fixture label in the full client capture.

## Frozen decision

PASS requires a valid measured client rectangle, both initial and post-action public captures matching that exact region, retained post-action image bytes matching the report's SHA-256, the full visible `VISUAL-R05` string in the screenshot, exact independent effect and event counts, completed public dispatch, verified all-up release, and clean owned-fixture exit. The structural auditor checks all recorded facts and image integrity; the visual text check is a separate review of the retained screenshot and will be recorded with its SHA-256. Any failed or unknown outcome remains preserved without replay.

The result is one positive-path local fixture sample. It does not prove blocked-I/O release bounds, supervisor recovery, atomic generation fencing, MAP01, matched efficiency, or broad reliability.

## Frozen R05 outcome

The probe measured a 404x181 client rectangle and used that exact region for both public captures. The dispatch completed once with the observed target generation forwarded. The independent effect file and event journal match `VISUAL-R05` exactly, with one click and one save; the release receipt is verified with empty down/unknown key and button sets, and the fixture exited 0. The frozen structural auditor passes 29/29.

The retained 404x181 post-action image is SHA-256 `68242cb349f04a65439ea55650dc86a6c39360765d302a32b69a85764649e8eb`; its artifact and source-frame hashes match the public report. Visual review confirms the entire `VISUAL-R05` sentinel is visible after the fixture label. See `visual_review.json` for the review record.

The high-resolution timing sample measured click-to-save file close at 59.7386 ms from public dispatch start, public response at 129.0408 ms, save-write close in 0.3099 ms, independent read beginning 116.0156 ms after file close, and a 4.2663 ms read. These are one-host, one-task values, not a comparison or performance distribution. Exact release sub-call time, blocked-I/O bounds, recovery, atomic target fencing, MAP01, matched efficiency, and broad reliability remain open.
