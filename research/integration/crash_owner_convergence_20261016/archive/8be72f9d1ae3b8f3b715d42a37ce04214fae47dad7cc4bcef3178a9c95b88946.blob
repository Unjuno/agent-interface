# Executor Child Hard-Kill with Persistent InputOwner A03

**Formal status: STOP.** This successor fixed A02's owner record reference. Raw evidence confirms SIGKILL of the Executor child, supervisor RPC EOF, verified InputOwner close/release with empty keys, X-server keymap-up, and owner thread stopped. However, the independent X event connection captured no KeyRelease. Source inspection found it subscribed with `event_mask=sum(types)`, where `types` are X event numbers rather than X event-mask bits. The preregistered independent-event gate is therefore not met. No candidate rerun; A04 corrects the event mask.

This is positive owner/keymap evidence but does not pass the complete registered gate. See the auditor and raw artifact.
