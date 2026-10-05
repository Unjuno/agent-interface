from collections.abc import Mapping


UNKNOWN = "UNKNOWN_INCOMPLETE_COVERAGE"


def _unknown(reason):
    return {"status": UNKNOWN, "reason": reason}


def certify_from_pages(pages, query):
    """Issue a scoped negative only for a complete, coherent versioned inventory."""
    if not isinstance(pages, (list, tuple)) or not pages:
        return _unknown("no_pages")
    if not isinstance(query, str) or not query:
        return _unknown("invalid_query")
    if not all(isinstance(p, Mapping) for p in pages):
        return _unknown("invalid_page")

    first = pages[0]
    required = ("schema", "surface_id", "epoch", "page_index", "page_count",
                "universe_complete", "writer_coverage", "predicate_version", "items")
    if any(any(key not in p for key in required) for p in pages):
        return _unknown("missing_field")
    if any(p["schema"] != "inventory.v1" for p in pages):
        return _unknown("unsupported_schema")
    if not isinstance(first["surface_id"], str) or not first["surface_id"]:
        return _unknown("invalid_surface")
    if type(first["epoch"]) is not int:
        return _unknown("invalid_epoch")
    if type(first["page_count"]) is not int or first["page_count"] < 1:
        return _unknown("invalid_page_count")

    page_count = first["page_count"]
    indexes = []
    objects = []
    for p in pages:
        if (p["surface_id"] != first["surface_id"] or p["epoch"] != first["epoch"]
                or p["page_count"] != page_count
                or p["predicate_version"] != first["predicate_version"]):
            return _unknown("scope_or_epoch_drift")
        if p["universe_complete"] is not True or p["writer_coverage"] is not True:
            return _unknown("producer_did_not_assert_complete_coverage")
        if type(p["page_index"]) is not int or not isinstance(p["items"], list):
            return _unknown("invalid_page_contents")
        indexes.append(p["page_index"])
        objects.extend(p["items"])

    if len(pages) != page_count or sorted(indexes) != list(range(page_count)):
        return _unknown("missing_or_duplicate_page")

    seen = set()
    for obj in objects:
        if (not isinstance(obj, Mapping) or not isinstance(obj.get("id"), str)
                or not obj["id"] or not isinstance(obj.get("label"), str)):
            return _unknown("invalid_object")
        if obj["id"] in seen:
            return _unknown("duplicate_object_identity")
        seen.add(obj["id"])

    matches = [obj for obj in objects if obj["label"].casefold() == query.casefold()]
    if matches:
        return {"status": "MATCH_FOUND", "match": dict(matches[0]),
                "scope": {"surface_id": first["surface_id"], "epoch": first["epoch"]}}

    return {
        "status": "NO_MATCH_WITHIN_CERTIFIED_SCOPE",
        "scope": {
            "surface_id": first["surface_id"],
            "epoch": first["epoch"],
            "predicate_version": first["predicate_version"],
            "page_count": page_count,
        },
        "linearization_point": "single_versioned_inventory_epoch",
        "item_count": len(objects),
    }
