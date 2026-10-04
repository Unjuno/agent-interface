"""Construction-only paired-frame invalidation for health/ammo cover guards."""


def evaluate_pair(health_guard, ammo_guard, health, ammo):
    """Fail closed unless both typed signals identify one observation frame."""
    identity_fields = ("sequence", "capture_ns", "binding")
    if any(health.get(field) != ammo.get(field) for field in identity_fields):
        return {
            "status": "PAIR_MISMATCH",
            "requires_new_decision": True,
            "grants_input_authority": False,
        }
    outcomes = {
        "health": health_guard.evaluate(health),
        "ammo": ammo_guard.evaluate(ammo),
    }
    return {
        "status": "PAIRED",
        "outcomes": outcomes,
        "requires_new_decision": any(
            outcome["requires_new_decision"] for outcome in outcomes.values()
        ),
        "grants_input_authority": False,
    }
