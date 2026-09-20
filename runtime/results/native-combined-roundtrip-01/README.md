# Combined send/read orchestration: one live Inkscape run

Source 48c717f5e, WSL Inkscape seed 991123, two stages, text gap 0. The primary
assistant issued native_start and two native_submit calls using one functions
invocation per request. Each invocation awaited write_stdin, then ran the exact
response-ID reader and forwarded returned image blocks. The assistant received
and viewed the image before authoring the next request. No next GUI action was
chosen inside the orchestration code.

Both immutable action requests match the prior recheck trial. Three exact images
show initial geometry, X=62 after selection/movement and saved X=74, Y=50,
width=40, height=30. Task evaluation, feedback and cleanup completed. The final
submit carried owner PID 20808 terminal/exit 0, so no status call was needed.
Relay session 27080 exited 0 after EOF.

This used three outer orchestration invocations for start/submits instead of the
separate send and read invocations previously used for each of these requests.
The six nested tool operations and response JSONL file remain. Counts describe
the primary assistant's recorded invocation structure, not model inference calls
or data measured by the server. Relay launch and EOF are outside that count.

The timing reader reports 32.380313966 s from first SDK entry to final return,
5.842264264 s inside SDK calls and 26.538049702 s between calls. This is not a
matched model/context/code comparison or a causal speedup. It does not measure
host image delivery, model tokens/cost or human performance. Direct registered
MCP use is still unverified. Do not compare the different Calc task's duration
as if it were a baseline for this Inkscape run.

The retained reader accepts only complete lines and an exact response ID.
A reader timeout must lead to another read of the same response/owner, never
re-execution of the combined send/read block: its send has already happened.
Do not truncate base64 payloads or forward terminal-rendered echoed JSON.

Run audit.py for manifest hashes, request identity, three image payloads,
continuation/source linkage, geometry, releases and terminal status. This is a
same-assistant artifact audit, not independent evaluation. The manifest covers
all files except itself. No sensor, automatic action replay, Docker restart or
container execution was introduced.
