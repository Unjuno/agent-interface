# E05 close-safe preparation, not a formal native experiment

H: E04 lost RESULT because Xlib close runs after the owned Xvfb server retires
and an uncaught exception aborts the rest of finally.
T: Fresh real Xvfb with two actual Xlib clients, compare server-first close
against clients-first close; result writing must survive failures and preserve
both cleanup errors. This probe never runs E03/E04 game or official auditor.
D: Exact source/image, test commands/logs, container inspect and RED/GREEN.
C: clients-first close must retain empty cleanup_faults. server-first must
retain two ConnectionClosedError entries, not suppress or relabel them.
U: No keys/game/model/physical release or scientific fault/cancel PASS. Formal
E05 native allocation remains ZERO until full runner/auditor freeze and review.

Additive branch research/v39-close-prep-e05-3cbf-20261004.
Consumed E04 code/results remain unchanged. Own private VM and pinned image
560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b only.
This repairs a prerequisite of the existing Issue59 question, not a new Issue.
