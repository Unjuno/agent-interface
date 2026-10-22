# continuation33: explicit-device wire construction

Worker 01a0ff2c-34fb-73a0-b3aa-bdf13badf325, FINAL-v5; parent #57/#7148.
Ordinary isolated construction, no formal/native allocation, no production edit.

H: the standard XI1 XTEST device-button encoding removes ClientPointer routing from a single request for a stable, known device ID. Merely filling deviceid in a core request does not. Explicit ID does not establish generation or per-client ownership.
T: use Python-Xlib0.33's real rq request encoder with a private request definition derived from official xorgproto2024.1 and libXtst1.2.5 source. An independent struct decoder checks every byte. A declared inert routing oracle implements the two branches in pinned server xtest.c. Check core-with-ID negative, explicit routing through a pointer switch and ABA, invalid ID rejection, and ID reuse residual. One finite child, 30s/output bounds.
D: exact36-byte header/event/device offset required; explicit request must target7 regardless of ClientPointer2/4; core negative must target current pointer; unsafe IDs rejected before request. The ID reuse witness must show an explicit release reaching replacement generation, keeping adoption HOLD. Any unexpected assertion failure is retained, not excluded.
C/U: no real libXtst C execution, no X server, no native socket, no physical input, no full backend integration. Event base64/opcode132 are declared test values, not deployment observations. Routing oracle is source-based and cannot qualify actual effects. Device7 denotes a known intended synthetic source; resolving it from actual topology remains unimplemented. Shared XTEST-device presses from other clients remain an ownership problem.

Official archives: https://xorg.freedesktop.org/archive/individual/lib/libXtst-1.2.5.tar.xz and https://xorg.freedesktop.org/archive/individual/proto/xorgproto-2024.1.tar.xz . Original license headers and COPYING retained. Archives hash-pinned locally; signature authenticity not verified.
No GitHub write before21:50UTC; previous unknown capsule POST remains unconfirmed. V4 adoption/application HOLD remains. main/head read33: main13cd5f3dcdf43bfc2c6153e489753dd9f1077861; V4ed7bb24e45fac16114e1247e00c8ed86cebda5c8 open/draft/unmerged. Six startup document blob IDs unchanged from32.
