# Native Codex single-image grounding pilot

One preregistered, no-GUI-action model turn used the existing WSL-to-Windows direct app-server command with `gpt-6.1-sol`, low effort, against the retained synthetic Chromium screenshot. The returned field [235,402] and submit [386,402] are visually inside the field and button in this screenshot; this is a manual visual check, not an independent executed task-effect oracle. The model returned a valid compiled-grounding response and the app-server session closed.

Reported usage: 12,244 input tokens (0 cached), 113 output tokens (0 reasoning subset), 0 cache-write input tokens. Grounding call time was 4.249779307 seconds. These are one provider attempt, not a speed comparison, cost estimate, or general accuracy/reliability claim. No GUI input or recovery was attempted.

The raw screenshot, prompt, result, summarized usage, conditions and probe are retained here. The full protocol journal contains local paths and remains in the local experiment directory; only its SHA-256 and byte count are retained here. Credentials were not copied. The five checked source files were LF-equivalent, not byte-identical, to the direct executable adapter sources at main `b321030c75cb96dac542033ee692610e1dcd580b`. The WSL-hosted model path is not yet connected to the isolated WSLc GUI caller.
