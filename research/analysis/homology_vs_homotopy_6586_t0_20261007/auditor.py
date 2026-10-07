"""Independent raw-only geometry and word-boundary auditor."""
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path


def inverse(symbol):
    return symbol.swapcase()


def normalize(word):
    changed = True
    current = word
    while changed:
        changed = False
        reduced = []
        i = 0
        while i < len(current):
            if i + 1 < len(current) and current[i + 1] == inverse(current[i]):
                i += 2
                changed = True
            else:
                reduced.append(current[i])
                i += 1
        current = "".join(reduced)
    return current


def abelianize(word, generators):
    result = []
    for generator in generators:
        result.append(sum(1 if c == generator else -1 if c == generator.upper() else 0 for c in word))
    return result


def words(alphabet, maximum):
    result = [""]
    for n in range(1, maximum + 1):
        result.extend("".join(p) for p in itertools.product(alphabet, repeat=n))
    return result


def build_path(word, fixture):
    p = [tuple(x) for x in fixture["generator_loops"]["a"]]
    q = [tuple(x) for x in fixture["generator_loops"]["b"]]
    base = tuple(fixture["basepoint"])
    route = [base]
    for char in word:
        segment = p if char.lower() == "a" else q
        if char.isupper():
            segment = segment[::-1]
        route += segment[1:]
    route += [tuple(fixture["common_tail"][1])]
    return route


def cuts_seen(route, fixture):
    result = []
    for first, second in zip(route, route[1:]):
        for cut in fixture["cuts"]:
            cx = cut["x"]
            if first[1] == second[1] and first[1] > cut["y_min"] and min(first[0], second[0]) < cx < max(first[0], second[0]):
                positive = second[0] < first[0] if cut["positive_direction"] == "right_to_left" else second[0] > first[0]
                result.append(cut["generator"] if positive else cut["generator"].upper())
    return "".join(result)


def segment_hits_rect(p, q, rect):
    xmin, ymin, xmax, ymax = rect
    if p[1] == q[1]:
        return ymin <= p[1] <= ymax and max(min(p[0], q[0]), xmin) < min(max(p[0], q[0]), xmax)
    if p[0] == q[0]:
        return xmin <= p[0] <= xmax and max(min(p[1], q[1]), ymin) < min(max(p[1], q[1]), ymax)
    return True


def independently_free(route, fixture):
    return all(not segment_hits_rect(p, q, rect) for p, q in zip(route, route[1:]) for rect in fixture["obstacles"])


def audit(raw, fixture):
    errors = []
    expected_words = words(fixture["alphabet"], fixture["max_word_length"])
    by_word = {row.get("word"): row for row in raw.get("rows", [])}
    if len(by_word) != len(expected_words) or set(by_word) != set(expected_words):
        errors.append("two_obstacle_denominator")
    groups = defaultdict(set)
    for word in expected_words:
        route = build_path(word, fixture)
        if not independently_free(route, fixture):
            errors.append("route_intersects_obstacle:" + word)
        seen = cuts_seen(route, fixture)
        reduced = normalize(seen)
        vector = abelianize(seen, ["a", "b"])
        row = by_word.get(word, {})
        if row.get("crossing_word") != seen or row.get("reduced") != reduced or row.get("homology") != vector:
            errors.append("raw_reconstruction:" + word)
        if row.get("complete") is not True or row.get("topology_version") != fixture["topology_version"]:
            errors.append("route_provenance:" + word)
        groups[tuple(vector)].add(reduced)
    r1expected = words(["a", "A"], fixture["rank1_max_word_length"])
    r1map = {row.get("word"): row for row in raw.get("rank1_rows", [])}
    if len(r1map) != len(r1expected) or set(r1map) != set(r1expected):
        errors.append("one_obstacle_denominator")
    rank1groups = defaultdict(set)
    for word in r1expected:
        reduced = normalize(word)
        vector = abelianize(word, ["a"])
        row = r1map.get(word, {})
        if row.get("reduced") != reduced or row.get("homology") != vector or row.get("complete") is not True:
            errors.append("one_obstacle_reconstruction:" + word)
        rank1groups[tuple(vector)].add(reduced)
    if len(rank1groups) != 1 + 2 * fixture["rank1_max_word_length"]:
        errors.append("rank1_signature_control")
    summary = raw.get("two_obstacle_summary", {})
    rank1_summary = raw.get("one_obstacle_summary", {})
    if summary.get("words") != len(expected_words) or summary.get("homology_buckets_with_multiple_homotopy_words") != sum(len(s) > 1 for s in groups.values()):
        errors.append("two_obstacle_summary_reconstruction")
    if rank1_summary.get("words") != len(r1expected) or rank1_summary.get("homology_buckets_with_multiple_homotopy_words") != sum(len(s) > 1 for s in rank1groups.values()):
        errors.append("rank1_summary_reconstruction")
    controls = {row.get("id"): row for row in raw.get("controls", [])}
    expected_control = {
        "commutator_collision": ("COMPARE", True, False, "", "abAB"),
        "adjacent_inverse_cancellation": ("COMPARE", True, True, "", ""),
        "same_word_different_route_length": ("COMPARE", True, True, "a", "a"),
        "unfinished_prefix": ("UNKNOWN", None, None, None, None),
        "missing_crossing_receipt": ("UNKNOWN", None, None, None, None),
        "geometry_revision": ("UNKNOWN", None, None, None, None)
    }
    if set(controls) != set(expected_control):
        errors.append("control_denominator")
    for key, wanted in expected_control.items():
        row = controls.get(key, {})
        observed = (row.get("decision"), row.get("homology_equal"), row.get("homotopy_equal"), row.get("left_reduced"), row.get("right_reduced"))
        if observed != wanted:
            errors.append("control:" + key)
    commutator = controls.get("commutator_collision", {})
    if commutator.get("homology_equal") is not True or commutator.get("homotopy_equal") is not False:
        errors.append("commutator_must_witness_kernel_of_abelianization")
    return {"audit_status": "PASS" if not errors else "FAIL", "errors": errors,
            "two_obstacle_words": len(by_word), "two_obstacle_signature_buckets_with_distinct_reduced_words": sum(len(s) > 1 for s in groups.values()),
            "one_obstacle_words": len(r1map), "one_obstacle_signature_buckets_with_distinct_reduced_words": sum(len(s) > 1 for s in rank1groups.values()),
            "commutator_signature": abelianize("abAB", ["a", "b"]), "commutator_reduced": normalize("abAB")}


def main():
    root = Path(__file__).resolve().parent
    raw = json.loads(Path(sys.argv[1]).read_text())
    fixture = json.loads((root / "fixture.json").read_text())
    result = audit(raw, fixture)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["audit_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
