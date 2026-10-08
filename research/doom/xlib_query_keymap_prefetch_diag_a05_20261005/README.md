# Python-Xlib query-keymap prefetch diagnostic A05

A05 is a one-shot isolated Xvfb diagnostic. It follows A04, which completed setup but deliberately did not invoke its candidate because that frozen trace recorded queue depth without event identities before `select()`. A05 records a serialized snapshot of every event already in Python-Xlib's internal queue before select and independently requires the exact expected client key event to appear in that snapshot. Events lacking `detail` are retained safely. A01–A04 outcomes remain under `predecessor/`.

This tests Python-Xlib/Xvfb only. It does not test V39, a game, a model, task effect, threat response, recovery, or MAP01.
