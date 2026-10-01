# Explicit observation in Calc: saved task succeeds, visual feedback unresolved

On source 19f87f988 the primary assistant used one fresh WSL Calc allocation,
seed 991124, max stages 4 and text gap 2 ms. The initial input request is byte
identical to the preceding failed Calc trial: enter A1=660, A2=811 and Save.
The returned image again showed a partially painted format dialog. This time
the assistant submitted interaction=observe at stage 2 / source sequence 5.

That request returned one newly captured image at sequence 6 without target
minting or an input program. The image showed the cells and fully painted Use
Excel 2007-365 Format button. The assistant chose that visible button at
[783,463] with finish_after. The saved workbook independently reads A1=660,
A2=811, B1 empty. Evaluation reports success, cleanup completed and the final
process snapshot reports PID 20433 terminal / exit 0. Relay session 61528 then
closed on EOF with exit 0. No separate native_status request was needed.

There are four requests: start, input, observation, confirmation input. This is
not a speed or roundtrip improvement over a successful two-action Calc baseline;
it demonstrates the missing input-free recovery path on a new trial. The prior
failed trial remains intact. The returned final image still shows a save-progress
dialog and feedback is needs_review; do not claim visual completion or infer it
from the successful saved-file score. The file, visual feedback and process
outcomes intentionally remain separate.

Run audit.py with Python/openpyxl to verify all four image payloads, hashes,
request/reply and continuation linkage, the lack of a stage-2 mint/input program,
new capture identity, released input, saved cells and terminal state. The
manifest covers all files except itself. This same-assistant audit checks
retained artifacts, not an independent review or a new application execution.
No sensor, background polling, automatic replay, Docker restart or container
execution was added. Human-tempo performance and model token/cost are unmeasured.
