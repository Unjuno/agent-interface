# Direct primary-agent MCP use: Calc

This retained WSL run demonstrates the primary agent using the exposed research
MCP tools directly to enter A1=893 and A2=758 and save an XLSX file. It is a
single integration observation, not a speed comparison or formal adoption result.
No secondary model, sensor implementation, Docker restart, or input replay was used.

The allocation used Calc, seed 991125, text gap 2 ms and a maximum of eight stages.
The agent viewed the initial image, submitted the two values and Ctrl+S as one
keyboard batch, and received a partially painted format dialog. An explicit
observation stage returned the completed dialog. The agent then used Return on
the focused Excel-format button with finish_after=true.

The final evaluator reported success. A separate read-only openpyxl load of the
retained sheet.xlsx confirmed [893, 758]. Both action receipts reported verified
input release. The last feedback step reported needs_review with BadWindow as
the dialog disappeared. The final screenshot still contains dialog pixels even
though its binding names the main window; screenshot paint completion and window
identity must not be treated as equivalent. No visual disappearance is claimed.

The managed MCP response and subsequent status read reported terminal, PID 26456,
return code 0. Its task_success=null is process-only information, not a reversal
of the receipt's evaluation.success=true. Cleanup reported tracked processes
terminal, but owner_exit_verified and descendants_verified remained false.
Complete cleanup verification is not claimed.

## Evidence and limits

RESULT.json inventories SHA256 and size for all 55 archived files. evidence.tar.gz
contains the original requests, replies, captures, workbook, launch information,
stdout/stderr and primary-direct-mcp-calls.json. The latter preserves native_start
and all three native_submit tool responses, including image blocks. Additional
read-only native_observe and native_status calls were not captured in that file;
it is not a complete conversation trace. No archive audit rewrites the raw files.

The research checkout HEAD was inspected after the run as 316beed02f8a8fe345a7079d5f72ad54badde749.
There was no full launch-time source attestation, so this is not an exact-main
benchmark. The allocation ran from the research checkout, not the public main
checkout. Model input tokens, cost, useful-feedback latency and human-comparable
tempo were not measured. This remains draft integration evidence pending review.

The next integration concern is preserving these separate facts clearly for the
caller: dispatched input, saved task result, window transition feedback, and
process cleanup. The observation stage was an existing tool capability; no new
sensor design or sensor experiment is included.
