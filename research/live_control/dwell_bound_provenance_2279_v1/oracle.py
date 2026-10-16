"""Fail-closed provenance contract for the dwell-timeout upper bound M."""
from dataclasses import dataclass
from math import isfinite
@dataclass(frozen=True)
class BoundCertificate:
    upper_bound: float
    source_id: str | None
    trusted: bool
def certify_bound(certificate: BoundCertificate) -> tuple[str, float | None]:
    if certificate.source_id is None or not certificate.source_id.strip(): return "UNKNOWN_BOUND", None
    if not certificate.trusted: return "UNKNOWN_BOUND", None
    if not isfinite(certificate.upper_bound) or certificate.upper_bound <= 0: return "INVALID_BOUND", None
    return "TRUSTED_BOUND", certificate.upper_bound
