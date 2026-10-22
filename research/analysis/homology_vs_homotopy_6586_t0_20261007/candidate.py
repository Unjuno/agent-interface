"""Finite crossing-word and abelian-signature candidate; stdlib only."""
import itertools
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
INV = {"a": "A", "A": "a", "b": "B", "B": "b"}


def reduce_word(word):
    stack = []
    for symbol in word:
        if stack and INV[symbol] == stack[-1]:
            stack.pop()
        else:
            stack.append(symbol)
    return "".join(stack)


def signature(word):
    return [word.count("a") - word.count("A"), word.count("b") - word.count("B")]


def path_for(word, fixture):
    loops = fixture["generator_loops"]
    points = [tuple(fixture["basepoint"])]
    for symbol in word:
        loop = loops[symbol.lower()]
        if symbol.isupper():
            loop = list(reversed(loop))
        points.extend(tuple(p) for p in loop[1:])
    points.extend(tuple(p) for p in fixture["common_tail"][1:])
    return points


def crossings(points, fixture):
    events = []
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if y1 == y2:
            for cut in fixture["cuts"]:
                x = cut["x"]
                if min(x1, x2) < x < max(x1, x2) and y1 > cut["y_min"]:
                    positive = (x2 < x1) == (cut["positive_direction"] == "right_to_left")
                    symbol = cut["generator"] if positive else cut["generator"].upper()
                    events.append(symbol)
    return "".join(events)


def all_words(alphabet, maximum):
    yield ""
    for length in range(1, maximum + 1):
        for symbols in itertools.product(alphabet, repeat=length):
            yield "".join(symbols)


def analyze(fixture):
    rows = []
    buckets = defaultdict(set)
    for word in all_words(fixture["alphabet"], fixture["max_word_length"]):
        crossing_word = crossings(path_for(word, fixture), fixture)
        reduced = reduce_word(crossing_word)
        vector = signature(crossing_word)
        rows.append({"word": word, "crossing_word": crossing_word, "reduced": reduced,
                     "homology": vector, "complete": True, "topology_version": fixture["topology_version"]})
        buckets[tuple(vector)].add(reduced)
    rank1 = []
    for word in all_words(["a", "A"], fixture["rank1_max_word_length"]):
        rank1.append({"word": word, "reduced": reduce_word(word), "homology": [word.count("a") - word.count("A")], "complete": True})
    rank1_buckets = defaultdict(set)
    for row in rank1:
        rank1_buckets[tuple(row["homology"])].add(row["reduced"])
    controls = []
    for item in fixture["controls"]:
        if not item["complete"] or not item.get("receipt_complete", True) or item["topology_version"] != fixture["topology_version"]:
            controls.append({"id": item["id"], "decision": "UNKNOWN"})
            continue
        left, right = item["left"], item["right"]
        controls.append({"id": item["id"], "decision": "COMPARE",
                         "homology_equal": signature(left) == signature(right),
                         "homotopy_equal": reduce_word(left) == reduce_word(right),
                         "left_reduced": reduce_word(left), "right_reduced": reduce_word(right)})
    return {"allocation": fixture["allocation"], "rows": rows, "rank1_rows": rank1,
            "two_obstacle_summary": {"words": len(rows), "homology_buckets_with_multiple_homotopy_words": sum(len(v) > 1 for v in buckets.values())},
            "one_obstacle_summary": {"words": len(rank1), "homology_buckets_with_multiple_homotopy_words": sum(len(v) > 1 for v in rank1_buckets.values())},
            "controls": controls}


def main():
    fixture = json.loads((HERE / "fixture.json").read_text())
    print(json.dumps(analyze(fixture), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
