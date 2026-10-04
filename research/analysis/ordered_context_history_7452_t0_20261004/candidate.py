"""Deterministic candidate generator. Emits raw rows, not a PASS judgment."""
import json
from itertools import product
from pathlib import Path

import model


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    factor_rows = [(c, ("OBSERVE", "OBSERVE")) for c in model.context_cover()]
    # Keep event-only rows in a distinct reset stratum from the context array.
    event_rows = [((0, 0, 1), h) for h in model.PAIR_HISTORIES]
    # Equal-budget separate baseline: keep the two certificates separate and
    # add legal fixed-context histories; none crosses context(1,1) with R->A.
    triples = [h for h in product(model.EVENTS, repeat=3) if model.legal(h)]
    padding = [((0, 0, 0), h) for h in triples[:26]]
    baseline = factor_rows + event_rows + padding
    mixed = [((f, s, 0), h) for f, s in model.PAIR_CONTEXTS
             for h in model.PAIR_HISTORIES]
    raw = {
        "schema": "ordered-context-history-7452-t0-v1",
        "rows": [{"suite": suite, "context": list(c), "history": list(h)}
                 for suite, rows in (("separate_equal_budget", baseline),
                                     ("mixed_occ", mixed))
                 for c, h in rows],
        "fixture": {"contexts": [list(c) for c in model.CONTEXTS],
                    "pair_histories": [list(h) for h in model.PAIR_HISTORIES],
                    "context_cover": [list(c) for c in model.context_cover()],
                    "legal_rule": "RELEASE requires prior ACT; one release maximum; no ACT after RELEASE; each row is a reset episode"}
    }
    (out / "candidate.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return raw


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
