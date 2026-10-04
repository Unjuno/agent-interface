"""Promoted platform-neutral Agent Interface runtime kernel v1."""

from .backend import BackendRegistry
from .contracts import (
    Action,
    ActionKind,
    AuthorityLease,
    BackendInfo,
    Capability,
    ContractError,
    EffectOccurrence,
    EffectReceipt,
    EffectStatus,
    ExecutionReceipt,
    ExecutionRequest,
    Observation,
    PlatformBackend,
    ReleaseReceipt,
    SupportLevel,
    TargetBinding,
)
from .lifecycle import KernelOutcome, RequestLifecycle, Stage

__all__ = [
    "Action", "ActionKind", "AuthorityLease", "BackendInfo", "BackendRegistry",
    "Capability", "ContractError", "EffectOccurrence", "EffectReceipt",
    "EffectStatus", "ExecutionReceipt", "ExecutionRequest", "KernelOutcome",
    "Observation", "PlatformBackend", "ReleaseReceipt", "RequestLifecycle",
    "Stage", "SupportLevel", "TargetBinding",
]
