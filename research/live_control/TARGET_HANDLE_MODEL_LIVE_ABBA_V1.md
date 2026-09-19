# Target-handle model and live ABBA v1

This allocation asks whether a scoped target handle can remove repeated image
grounding without reducing correctness. It keeps requested Luna-low, Fast
disabled, a short GUI responder instruction file and one common structured
action envelope. Reported usage is the CLI turn-completed usage; served model
identity and monetary cost remain unavailable.

The first fixed-state screen retained an uncontrolled result: coordinate calls
reported12,583 input tokens each, while identical handle calls reported11,332
and54,244, including42,240 cached in the latter. A controlled-context follow-up
replaced the broad built-in instructions, disabled project-document loading,
used an empty workspace and fixed one output schema. Two schema attempts were
rejected before model execution because property types and a root object were
required. Both failures remain in target-handle-model-screen-02/03.

The corrected single-envelope screen passes all preregistered gates:

| Arm | Correct | Reported input | Within-arm range |
|---|---:|---:|---:|
| image coordinate | 2/2 | 9,268 each | 0 |
| no-image handle | 2/2 | 8,009 each | 0 |

The handle representation uses1,259 fewer reported input tokens,13.58%, on this
fixed archived action. No live input occurs in that screen.

The first fresh live driver fails before GUI/model work because Windows Python
cannot import the fcntl journal dependency. The corrected host boundary keeps
journal, X11 and GUI work under WSL and invokes only the model runner through
Windows Python. In that second allocation, coordinate sessions independently
save2/2, but handle sessions safely refuse2/2 with zero input: the runtime minted
a private random ID while the model returned the friendly name h_save_form.
This reveals that an opaque registry key is not a usable model-facing reference.

scoped_target_handle_v3 now maps one bounded, unique session alias such as
save_form to a private random registry ID. The random ID is not emitted.
Invalid, duplicate and unknown aliases are refused. Pure controls pass on
Windows and WSL. A read-only target_handle_query resolves the alias against
the current image without granting input authority; action admission resolves
it again against a post-model fresh observation.

The new-seed live ABBA passes every preregistered gate over four independent
Chromium submissions:

| Arm | Independent success | Input tokens | Decision start to evaluation return | Durable calls |
|---|---:|---:|---:|---:|
| image coordinate | 2/2 | 9,280 / 9,280 | 6.901s / 7.341s | 14 / 14 |
| no-image alias handle | 2/2 | 8,013 / 8,013 | 6.247s / 6.349s | 16 / 16 |

Both handle queries and both admission-time checks return REVALIDATED. All
four terminals release input, the exact generated token reaches the independent
HTTP/file oracle4/4, and62 frames replay exactly on Windows and WSL. Mean
reported input is1,267 tokens lower for handle,13.65%. Mean decision-to-evaluation
return is descriptively0.823s shorter, while handle adds two durable calls for
the explicit query.

Decision: advance the alias/query contract to a cross-domain replication, still
opt-in. Two cases per arm do not establish a latency distribution or causal
speedup. The box and alias are human-authored, the task is one repeated Chromium
form, cost is unavailable and the extra query is an ergonomics/round-trip debt.
The next design should attach watched-handle status to a normal observation or
batch multiple queries, then test a different domain without relaxing exact
matching or admission-time revalidation.
