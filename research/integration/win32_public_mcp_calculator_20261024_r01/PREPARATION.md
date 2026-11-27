# Win32 public MCP Calculator effect check — R01

This is one bounded native-Windows trial through the public `supervised-win32`
MCP server route. The user authorized this PC for experiments. The app is the
preinstalled Windows Calculator in Standard mode; no user files, browser data,
network service, WSLc allocation, or Docker container is used.

The fixed task is to compute `314 + 728` and observe `1042`. Before input, the
runner must use one fresh public `interface_observe` result, validate the exact
program once, and dispatch it once. The program clicks only the visible
Calculator buttons and ends with `release_all`. It may not retry, replay,
repair, or call recovery. The independent post-task check is a fresh screenshot
from outside the runtime. Preserve the runtime's raw observe, validation,
dispatch, result, close, and release/readback records, plus the app screenshot.

Stop on target mismatch, unexpected UI state, rejected validation, pending
delivery not resolved inside the five-poll budget, any error, or deadline. Keep
effect or release as UNKNOWN if evidence is incomplete. The result can qualify
only this one composed real-app success; it cannot qualify efficiency,
reliability, MAP01, blocked-OS-I/O release, or WSLc.
