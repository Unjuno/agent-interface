"""Promoted Agent Interface portable runtime contract v1.

This package contains OS-neutral admission semantics only. Native backends are
separate implementations and must not infer support from platform presence.
"""

from .contract import (
    Admission,
    ContractError,
    OFFICE_FLOOR,
    SCHEMA_BACKEND,
    SCHEMA_PROGRAM,
    admit_program,
    capability_manifest,
    office_readiness,
    required_capabilities,
    validate_backend_manifest,
    validate_program,
)
from .platform_probe import probe_platform

__all__ = [
    "Admission",
    "ContractError",
    "OFFICE_FLOOR",
    "SCHEMA_BACKEND",
    "SCHEMA_PROGRAM",
    "admit_program",
    "capability_manifest",
    "office_readiness",
    "probe_platform",
    "required_capabilities",
    "validate_backend_manifest",
    "validate_program",
]
