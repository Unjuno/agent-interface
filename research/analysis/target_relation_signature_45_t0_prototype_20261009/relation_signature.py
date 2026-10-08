"""Advisory same-session relation-signature revalidation prototype.

This module never authorizes input. Its string identifiers must come from the
same public observation boundary, not hidden scorer or app-internal state.
"""

from dataclasses import dataclass


_FIELDS = ("surface", "container", "role", "label", "relations", "generation", "complete")


@dataclass(frozen=True)
class Result:
    status: str
    candidate_index: int | None
    authority: str = "none"


def _valid_signature(value):
    if type(value) is not dict or any(key not in value for key in _FIELDS):
        return False
    if any(type(value[key]) is not str or not value[key] for key in
           ("surface", "container", "role", "label")):
        return False
    relations = value["relations"]
    if (type(relations) is not list or
            any(type(item) is not str or not item for item in relations) or
            len(set(relations)) != len(relations)):
        return False
    if type(value["generation"]) is not int or value["generation"] < 1:
        return False
    return type(value["complete"]) is bool


def revalidate(source, candidates, *, generation, complete):
    """Return an advisory status for a complete fresh observation.

    Exact relation matches are accepted only when unique. If the same
    surface/container/role/label remains but its relations changed, the result
    is UNKNOWN; this deliberately avoids treating reflow as identity proof.
    """
    if not _valid_signature(source) or source["complete"] is not True:
        return Result("INVALID", None)
    if type(generation) is not int or generation <= source["generation"]:
        return Result("STALE", None)
    if type(complete) is not bool or not complete or type(candidates) is not list:
        return Result("UNKNOWN", None)
    if any(not _valid_signature(item) or item["complete"] is not True
           for item in candidates):
        return Result("UNKNOWN", None)
    if any(item["generation"] != generation for item in candidates):
        return Result("STALE", None)

    hard_fields = ("surface", "container", "role", "label")
    compatible = [
        index for index, candidate in enumerate(candidates)
        if all(candidate[field] == source[field] for field in hard_fields)
    ]
    source_relations = frozenset(source["relations"])
    exact = [index for index in compatible
             if frozenset(candidates[index]["relations"]) == source_relations]
    if len(exact) > 1:
        return Result("AMBIGUOUS", None)
    if len(exact) == 1:
        return Result("REVALIDATED", exact[0])
    if compatible:
        return Result("UNKNOWN", None)
    return Result("NO_MATCH", None)
