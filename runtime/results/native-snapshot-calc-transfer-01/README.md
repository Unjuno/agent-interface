# Calc transfer failure: no supported input-free fresh observation path

On source f9a18383b the primary assistant used one fresh WSL Calc allocation,
seed 991124, max stages 4, text gap 2 ms. The initial public task specified
A1=660 and A2=811, saved as XLSX. The assistant viewed the initial sheet image
then explicitly typed both values and Save in one keyboard program.

Input completed and released keys/buttons. Feedback reported a binding change;
window review returned a source-4 image of a partially painted Confirm File
Format dialog, with its title visible but body not yet rendered. The assistant
did not guess a confirmation button. It submitted stage 2 / source 4 as keyboard
context with only wait_update(250). This was rejected by the existing bridge:
`keyboard continuation requires explicit keyboard input`. The harness terminated
with cleanup completed and no evaluation. native_status subsequently reported
owner PID 20238 exit 1; relay session 62616 closed with exit 0. No input replay,
restart or confirmation click occurred. Saved cell correctness is unproven.

This is a task failure, not a successful cross-application transfer. The second
request was an assistant API-use error: the existing keyboard method requires
keyboard input. It also reveals an interface gap: native_observe reads retained
images, and the caller lacks an explicit bounded fresh observation without
input. Do not work around this by sending a dummy key or guessing UI targets.
A future input-free observation operation must be distinguished from sensors,
keep exact stage/source references, and retain all timeout/cleanup outcomes.

The manifest covers retained files except itself. Raw response JSONL contains
two exact image blocks; the error response carries the prior action and cleanup
receipt without a new image. No complete task or latency/model-cost benefit is
claimed. The private allocation is terminal; it must not be restarted.
