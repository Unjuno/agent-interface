"""Fail-closed identity comparison used by the candidate bridge."""


def admit(alias, current):
    required = ("xid", "pid", "start_ticks", "geometry", "pixel_sha256")
    if any(alias.get(key) is None or current.get(key) is None for key in required):
        return False
    return all(alias[key] == current[key] for key in required)
