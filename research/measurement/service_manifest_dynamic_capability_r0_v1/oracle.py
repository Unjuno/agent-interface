from __future__ import annotations

def decide(current_scope,current_generation,current_caps,snap,requested,manifest_complete=True):
    if not manifest_complete: return 'MANIFEST_INCOMPLETE'
    if snap is None: return 'DISCOVER_CAPABILITIES'
    try:
        scope=snap['scope']; gen=snap['generation']; caps=set(snap['caps'])
    except Exception:
        return 'DISCOVER_CAPABILITIES'
    if scope != current_scope or gen != current_generation:
        return 'DISCOVER_CAPABILITIES'
    return 'SUPPORTED' if requested in caps else 'FALLBACK'
