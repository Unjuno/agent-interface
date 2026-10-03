"""Fail-closed mechanical request lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AuthorityLease,
    ContractError,
    EffectReceipt,
    EffectStatus,
    ExecutionReceipt,
    ExecutionRequest,
    Observation,
    ReleaseReceipt,
    TargetBinding,
)


class Stage(str, Enum):
    NEW = "new"
    OBSERVED = "observed"
    BOUND = "bound"
    AUTHORIZED = "authorized"
    EXECUTED = "executed"
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNAVAILABLE = "unavailable"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class KernelOutcome:
    stage: Stage
    reason: str
    command_id: str | None
    effect_occurred: bool
    effect_verified: bool
    release_verified: bool


class RequestLifecycle:
    def __init__(self) -> None:
        self.stage = Stage.NEW
        self.observation: Observation | None = None
        self.binding: TargetBinding | None = None
        self.lease: AuthorityLease | None = None
        self.request: ExecutionRequest | None = None
        self.execution: ExecutionReceipt | None = None
        self.effect: EffectReceipt | None = None
        self.stop_reason: str | None = None

    def record_observation(self, observation: Observation) -> None:
        if self.stage is not Stage.NEW:
            raise ContractError("observation can only be recorded from NEW")
        if not isinstance(observation, Observation):
            raise ContractError("observation must be Observation")
        self.observation = observation
        self.stage = Stage.OBSERVED

    def bind(self, binding: TargetBinding) -> None:
        if self.stage is not Stage.OBSERVED or self.observation is None:
            raise ContractError("binding requires one current observation")
        if binding.observation_sequence != self.observation.sequence:
            raise ContractError("binding is stale for current observation")
        if binding.surface_id != self.observation.surface_id:
            raise ContractError("binding refers to another surface")
        self.binding = binding
        self.stage = Stage.BOUND

    def authorize(self, lease: AuthorityLease, *, now_ns: int) -> None:
        if self.stage is not Stage.BOUND or self.binding is None:
            raise ContractError("authority requires a current binding")
        if type(now_ns) is not int or now_ns < 0:
            raise ContractError("now_ns must be nonnegative integer")
        if lease.observation_sequence != self.binding.observation_sequence:
            raise ContractError("lease is stale for bound observation")
        if lease.surface_id != self.binding.surface_id:
            raise ContractError("lease refers to another surface")
        if now_ns >= lease.valid_until_ns:
            raise ContractError("lease is already expired")
        self.lease = lease
        self.stage = Stage.AUTHORIZED

    def begin_execution(self, request: ExecutionRequest, *, now_ns: int) -> None:
        if self.stage is not Stage.AUTHORIZED or self.binding is None or self.lease is None:
            raise ContractError("execution requires active authority")
        if type(now_ns) is not int or now_ns < 0:
            raise ContractError("now_ns must be nonnegative integer")
        if now_ns >= self.lease.valid_until_ns:
            raise ContractError("authority expired before execution")
        if request.binding != self.binding or request.lease != self.lease:
            raise ContractError("execution request changed bound target or authority")
        self.request = request

    def record_execution(self, receipt: ExecutionReceipt) -> None:
        if self.stage is not Stage.AUTHORIZED or self.request is None:
            raise ContractError("execution receipt requires begun execution")
        request = self.request
        if receipt.command_id != request.command_id:
            raise ContractError("execution receipt command mismatch")
        if receipt.invariant_manifest_id != request.invariant_manifest_id:
            raise ContractError("execution receipt manifest mismatch")
        if receipt.lease_id != request.lease.lease_id:
            raise ContractError("execution receipt lease mismatch")
        if receipt.observation_sequence != request.binding.observation_sequence:
            raise ContractError("execution receipt observation mismatch")
        if receipt.surface_id != request.binding.surface_id:
            raise ContractError("execution receipt surface mismatch")
        if receipt.action_count != len(request.actions):
            raise ContractError("execution receipt action count mismatch")
        if not receipt.release.released:
            raise ContractError("terminal execution receipt requires verified empty release")
        self.execution = receipt
        self.stage = Stage.EXECUTED

    def record_effect(self, receipt: EffectReceipt) -> None:
        if self.stage is not Stage.EXECUTED or self.execution is None or self.request is None:
            raise ContractError("effect receipt requires completed released execution")
        if receipt.command_id != self.execution.command_id:
            raise ContractError("effect receipt command mismatch")
        if receipt.invariant_manifest_id != self.execution.invariant_manifest_id:
            raise ContractError("effect receipt manifest mismatch")
        self.effect = receipt
        self.stage = {
            EffectStatus.VERIFIED: Stage.VERIFIED,
            EffectStatus.CONTRADICTED: Stage.CONTRADICTED,
            EffectStatus.UNAVAILABLE: Stage.UNAVAILABLE,
        }[receipt.status]

    def stop(self, reason: str, *, release: ReleaseReceipt | None = None) -> None:
        if type(reason) is not str or not reason:
            raise ContractError("stop reason must be nonempty")
        if self.stage in {Stage.VERIFIED, Stage.CONTRADICTED, Stage.UNAVAILABLE, Stage.STOPPED}:
            raise ContractError("terminal lifecycle cannot be stopped again")
        if self.stage is Stage.AUTHORIZED:
            if release is None or not release.released:
                raise ContractError("stopping active authority requires verified empty release")
        if self.stage is Stage.EXECUTED and self.execution is not None and not self.execution.release.released:
            raise ContractError("executed lifecycle lacks verified release")
        self.stop_reason = reason
        self.stage = Stage.STOPPED

    def outcome(self) -> KernelOutcome:
        if self.stage not in {
            Stage.VERIFIED, Stage.CONTRADICTED, Stage.UNAVAILABLE, Stage.STOPPED
        }:
            raise ContractError("outcome requested before terminal state")
        command = self.request.command_id if self.request is not None else None
        occurrence = (
            self.execution is not None
            and self.execution.effect_occurrence.value in {"possible", "observed"}
        )
        verified = self.stage is Stage.VERIFIED
        release_verified = (
            self.execution.release.released if self.execution is not None else self.stage is Stage.STOPPED
        )
        reason = self.stop_reason or self.stage.value
        return KernelOutcome(
            stage=self.stage,
            reason=reason,
            command_id=command,
            effect_occurred=occurrence,
            effect_verified=verified,
            release_verified=release_verified,
        )
