"""Backend discovery without importing OS-specific implementations into the kernel."""
from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Callable

from .contracts import BackendInfo, ContractError, PlatformBackend, SupportLevel


Factory = Callable[[], PlatformBackend]


@dataclass(slots=True)
class BackendRegistry:
    _factories: dict[str, Factory]

    def __init__(self) -> None:
        self._factories = {}

    def register(self, platform: str, factory: Factory) -> None:
        if type(platform) is not str or not platform:
            raise ContractError("platform key must be nonempty")
        if platform in self._factories:
            raise ContractError(f"backend already registered for {platform}")
        if not callable(factory):
            raise ContractError("backend factory must be callable")
        self._factories[platform] = factory

    def create(self, platform: str | None = None) -> PlatformBackend:
        key = platform or sys.platform
        factory = self._factories.get(key)
        if factory is None:
            raise LookupError(f"no backend registered for platform {key!r}")
        backend = factory()
        info = backend.probe()
        if not isinstance(info, BackendInfo):
            raise ContractError("backend probe must return BackendInfo")
        if info.support is SupportLevel.UNAVAILABLE:
            raise RuntimeError(f"backend unavailable: {info.detail or info.backend_name}")
        return backend

    def probe(self, platform: str | None = None) -> BackendInfo | None:
        key = platform or sys.platform
        factory = self._factories.get(key)
        if factory is None:
            return None
        info = factory().probe()
        if not isinstance(info, BackendInfo):
            raise ContractError("backend probe must return BackendInfo")
        return info

    def registered_platforms(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
