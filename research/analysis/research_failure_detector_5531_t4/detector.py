"""Finite candidate rule for a declared hierarchical failure-domain cut."""


def decide(witnesses, current_generation, independence_depth, required_domains):
    if independence_depth < 1 or required_domains < 1:
        raise ValueError("independence_depth and required_domains must be positive")

    by_observer = {}
    for row in witnesses:
        if not isinstance(row, dict):
            continue
        observer = row.get("observer")
        path = row.get("domain_path")
        generation = row.get("generation")
        if (
            not isinstance(observer, str)
            or not observer
            or not isinstance(path, list)
            or len(path) < independence_depth
            or any(not isinstance(part, str) or not part for part in path)
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation != current_generation
            or row.get("kind") != "independent_crash_witness"
        ):
            continue

        domain = tuple(path[:independence_depth])
        by_observer.setdefault(observer, set()).add(domain)

    # Conflicting placement claims for one observer are ambiguous and contribute
    # no witness. Repeated claims for the same placement remain one observer.
    valid = {
        observer: next(iter(domains))
        for observer, domains in by_observer.items()
        if len(domains) == 1
    }
    domains = sorted(set(valid.values()))
    return {
        "state": "FAILED" if len(domains) >= required_domains else "SUSPECTED_UNAVAILABLE",
        "independent_domain_count": len(domains),
        "valid_witness_count": len(valid),
        "independent_domains": [list(domain) for domain in domains],
    }
