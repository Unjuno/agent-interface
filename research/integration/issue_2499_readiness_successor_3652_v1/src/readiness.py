"""Role-filtered, fail-closed X11 application window admission."""

ROLE_MARKERS = {
    "inkscape": ("inkscape ",),
    "calc": ("libreoffice calc",),
    "chromium": ('"chromium"',),
}


def matches_role(role, raw_properties):
    text = raw_properties.lower()
    if role == "calc" and "tip of the day" in text:
        return False
    return any(marker in text for marker in ROLE_MARKERS[role])


def resolve_candidates(role, candidates):
    matches = [item for item in candidates if matches_role(role, item.get("raw", ""))]
    if not matches:
        return {"status": "STOP_IDENTITY_MISSING", "matches": []}
    if len(matches) != 1:
        return {"status": "STOP_IDENTITY_AMBIGUOUS", "matches": matches}
    return {"status": "READY", "matches": matches}


def require_window(role, candidates):
    result = resolve_candidates(role, candidates)
    if result["status"] != "READY":
        raise RuntimeError(result["status"])
    return result["matches"][0]["window"]
