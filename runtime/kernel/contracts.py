"""Platform-neutral runtime contracts for Agent Interface.

These types carry mechanical evidence only. They intentionally do not grant model
semantic authority and do not infer task success from current state alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Protocol, runtime_checkable

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Malformed or internally inconsistent runtime evidence."""


class Capability(str, Enum):
    OBSERVE_SCREEN = "observe_screen"
    KEY_INPUT = "key_input"
    POINTER_INPUT = "pointer_input"
    TEXT_INPUT = "text_input"
    WINDOW_FOCUS = "window_focus"
    RELEASE_ALL = "release_all"


class SupportLevel(str, Enum):
    TESTED = "tested"
    EXPERIMENTAL = "experimental"
    UNAVAILABLE = "unavailable"


class ActionKind(str, Enum):
    KEY = "key"
    POINTER = "pointer"
    TEXT = "text"
    FOCUS = "focus"


class EffectOccurrence(str, Enum):
    NONE = "none"
    POSSIBLE = "possible"
    OBSERVED = "observed"


class EffectStatus(str, Enum):
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNAVAILABLE = "unavailable"


def _text(name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ContractError(f"{name} must be a nonempty string")


def _count(name: str, value: int, *, positive: bool = False) -> None:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ContractError(f"{name} must be a {qualifier} integer")


@dataclass(frozen=True, slots=True)
class BackendInfo:
    backend_name: str
    platform: str
    support: SupportLevel
    capabilities: frozenset[Capability]
    detail: str = ""

    def __post_init__(self) -> None:
        _text("backend_name", self.backend_name)
        _text("platform", self.platform)
        if not isinstance(self.support, SupportLevel):
            raise ContractError("support must be SupportLevel")
        if type(self.capabilities) is not frozenset or any(
            not isinstance(value, Capability) for value in self.capabilities
        ):
            raise ContractError("capabilities must be a frozenset[Capability]")
        if self.support is SupportLevel.UNAVAILABLE and self.capabilities:
            raise ContractError("unavailable backend cannot advertise capabilities")


@dataclass(frozen=True, slots=True)
class Observation:
    sequence: int
    captured_ns: int
    surface_id: str
    payload_sha256: str
    width: int
    height: int
    encoding: str

    def __post_init__(self) -> None:
        _count("sequence", self.sequence, positive=True)
        _count("captured_ns", self.captured_ns)
        _text("surface_id", self.surface_id)
        if type(self.payload_sha256) is not str or not _SHA256.fullmatch(self.payload_sha256):
            raise ContractError("payload_sha256 must be lowercase SHA-256 hex")
        _count("width", self.width, positive=True)
        _count("height", self.height, positive=True)
        _text("encoding", self.encoding)


@dataclass(frozen=True, slots=True)
class TargetBinding:
    target_id: str
    observation_sequence: int
    surface_id: str
    binding_digest: str

    def __post_init__(self) -> None:
        _text("target_id", self.target_id)
        _count("observation_sequence", self.observation_sequence, positive=True)
        _text("surface_id", self.surface_id)
        if type(self.binding_digest) is not str or not _SHA256.fullmatch(self.binding_digest):
            raise ContractError("binding_digest must be lowercase SHA-256 hex")


@dataclass(frozen=True, slots=True)
class AuthorityLease:
    lease_id: str
    observation_sequence: int
    surface_id: str
    valid_until_ns: int
    allowed_actions: frozenset[ActionKind]

    def __post_init__(self) -> None:
        _text("lease_id", self.lease_id)
        _count("observation_sequence", self.observation_sequence, positive=True)
        _text("surface_id", self.surface_id)
        _count("valid_until_ns", self.valid_until_ns, positive=True)
        if type(self.allowed_actions) is not frozenset or not self.allowed_actions:
            raise ContractError("allowed_actions must be a nonempty frozenset")
        if any(not isinstance(value, ActionKind) for value in self.allowed_actions):
            raise ContractError("allowed_actions must contain ActionKind values")


@dataclass(frozen=True, slots=True)
class Action:
    action_id: str
    kind: ActionKind
    operation: str

    def __post_init__(self) -> None:
        _text("action_id", self.action_id)
        if not isinstance(self.kind, ActionKind):
            raise ContractError("kind must be ActionKind")
        _text("operation", self.operation)


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    command_id: str
    invariant_manifest_id: str
    binding: TargetBinding
    lease: AuthorityLease
    actions: tuple[Action, ...]

    def __post_init__(self) -> None:
        _text("command_id", self.command_id)
        if type(self.invariant_manifest_id) is not str or not _SHA256.fullmatch(
            self.invariant_manifest_id
        ):
            raise ContractError("invariant_manifest_id must be lowercase SHA-256 hex")
        if not isinstance(self.binding, TargetBinding):
            raise ContractError("binding must be TargetBinding")
        if not isinstance(self.lease, AuthorityLease):
            raise ContractError("lease must be AuthorityLease")
        if type(self.actions) is not tuple or not self.actions:
            raise ContractError("actions must be a nonempty tuple")
        if any(not isinstance(action, Action) for action in self.actions):
            raise ContractError("actions must contain Action values")
        if self.binding.observation_sequence != self.lease.observation_sequence:
            raise ContractError("binding and lease observation sequence differ")
        if self.binding.surface_id != self.lease.surface_id:
            raise ContractError("binding and lease surface differ")
        disallowed = {action.kind for action in self.actions} - self.lease.allowed_actions
        if disallowed:
            raise ContractError(
                "action kind outside lease authority: "
                + ",".join(sorted(value.value for value in disallowed))
            )


@dataclass(frozen=True, slots=True)
class ReleaseReceipt:
    observed_ns: int
    verified: bool
    keys_down: tuple[str, ...] = ()
    buttons_down: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        _count("observed_ns", self.observed_ns)
        if type(self.verified) is not bool:
            raise ContractError("verified must be bool")
        if type(self.keys_down) is not tuple or any(type(v) is not str for v in self.keys_down):
            raise ContractError("keys_down must be tuple[str, ...]")
        if type(self.buttons_down) is not tuple or any(
            type(v) is not int or v < 0 for v in self.buttons_down
        ):
            raise ContractError("buttons_down must be tuple[nonnegative int, ...]")
        if self.verified and (self.keys_down or self.buttons_down):
            raise ContractError("verified release must report empty physical input")

    @property
    def released(self) -> bool:
        return self.verified and not self.keys_down and not self.buttons_down


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    command_id: str
    backend_receipt_id: str
    invariant_manifest_id: str
    lease_id: str
    observation_sequence: int
    surface_id: str
    started_ns: int
    ended_ns: int
    action_count: int
    effect_occurrence: EffectOccurrence
    release: ReleaseReceipt

    def __post_init__(self) -> None:
        for name, value in (
            ("command_id", self.command_id),
            ("backend_receipt_id", self.backend_receipt_id),
            ("lease_id", self.lease_id),
            ("surface_id", self.surface_id),
        ):
            _text(name, value)
        if type(self.invariant_manifest_id) is not str or not _SHA256.fullmatch(
            self.invariant_manifest_id
        ):
            raise ContractError("invariant_manifest_id must be lowercase SHA-256 hex")
        _count("observation_sequence", self.observation_sequence, positive=True)
        _count("started_ns", self.started_ns)
        _count("ended_ns", self.ended_ns)
        if self.ended_ns < self.started_ns:
            raise ContractError("ended_ns must not precede started_ns")
        _count("action_count", self.action_count, positive=True)
        if not isinstance(self.effect_occurrence, EffectOccurrence):
            raise ContractError("effect_occurrence must be EffectOccurrence")
        if not isinstance(self.release, ReleaseReceipt):
            raise ContractError("release must be ReleaseReceipt")


@dataclass(frozen=True, slots=True)
class EffectReceipt:
    command_id: str
    invariant_manifest_id: str
    observed_ns: int
    status: EffectStatus
    evidence_digest: str

    def __post_init__(self) -> None:
        _text("command_id", self.command_id)
        if type(self.invariant_manifest_id) is not str or not _SHA256.fullmatch(
            self.invariant_manifest_id
        ):
            raise ContractError("invariant_manifest_id must be lowercase SHA-256 hex")
        _count("observed_ns", self.observed_ns)
        if not isinstance(self.status, EffectStatus):
            raise ContractError("status must be EffectStatus")
        if type(self.evidence_digest) is not str or not _SHA256.fullmatch(self.evidence_digest):
            raise ContractError("evidence_digest must be lowercase SHA-256 hex")


@runtime_checkable
class PlatformBackend(Protocol):
    def probe(self) -> BackendInfo: ...
    def observe(self) -> Observation: ...
    def execute(self, request: ExecutionRequest) -> ExecutionReceipt: ...
    def release_all(self) -> ReleaseReceipt: ...
