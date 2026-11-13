"""Join independent expiry sampling and pending resolver evidence safely.

The sampler observes key state around the serialized lease deadline. The
resolver samples key state while polling one public call. These sources have
different timing and custody meaning and must never be conflated.
"""
from __future__ import annotations


def join_w_input_samples(resolver_report, expiry_report):
    """Return a provenance-labeled view without promoting missing data.

    If resolver samples exist, they remain authoritative for resolver-specific
    fields. Expiry samples are exposed separately and are never synthesized
    into resolver rows. Missing either report is represented explicitly.
    """
    resolver = resolver_report if type(resolver_report) is dict else None
    expiry = expiry_report if type(expiry_report) is dict else None
    resolver_samples = resolver.get("samples") if resolver else None
    expiry_samples = expiry.get("samples") if expiry else None
    if type(resolver_samples) is not list:
        resolver_samples = None
    if type(expiry_samples) is not list:
        expiry_samples = None
    return {
        "resolver": {
            "present": resolver is not None,
            "samples": resolver_samples,
            "sample_count": len(resolver_samples) if resolver_samples is not None else None,
            "observed_w_down_before_terminal": (
                resolver.get("observed_w_down_before_terminal") if resolver else None
            ),
            "terminal_w_down": resolver.get("terminal_w_down") if resolver else None,
            "claim": resolver.get("claim") if resolver else None,
        },
        "expiry_sampler": {
            "present": expiry is not None,
            "samples": expiry_samples,
            "sample_count": len(expiry_samples) if expiry_samples is not None else None,
            "boundary_status": expiry.get("status") if expiry else None,
            "lease_deadline_ns": expiry.get("lease_deadline_ns") if expiry else None,
        },
        "classification": (
            "BOTH_PRESENT" if resolver is not None and expiry is not None
            else "BOTH_MISSING" if resolver is None and expiry is None
            else "RESOLVER_MISSING" if resolver is None
            else "EXPIRY_SAMPLER_MISSING" if expiry is None
            else "UNCLASSIFIED"
        ),
    }
