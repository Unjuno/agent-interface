"""Model-facing session aliases backed by private random target-handle IDs."""
import re

from scoped_target_handle_v2 import TargetHandleStore as Previous


ALIAS = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class TargetHandleStore(Previous):
    """Expose bounded unique aliases while retaining private random registry keys."""

    def __init__(self, session_scope, id_factory=None):
        super().__init__(session_scope, id_factory=id_factory)
        self._aliases = {}

    def mint(self, name, coordinate_frame, box, observation, image, now_ns,
             ttl_ms=30000, freshness_ms=1000, search_radius=0,
             allowed_transformations=("window_translation",)):
        if type(name) is not str or ALIAS.fullmatch(name) is None:
            raise ValueError("target alias must match [a-z][a-z0-9_]{0,31}")
        if name in self._aliases:
            raise ValueError("target alias already exists in this session")
        result = super().mint(
            name, coordinate_frame, box, observation, image, now_ns,
            ttl_ms, freshness_ms, search_radius, allowed_transformations
        )
        private = result["handle"]
        self._aliases[name] = private
        return {
            **result,
            "handle": name,
            "reference_kind": "session_alias",
            "private_registry_id_exposed": False,
        }

    def resolve_point(self, handle_id, offset, observation, image, now_ns,
                      session_scope=None):
        if type(handle_id) is not str or handle_id not in self._aliases:
            return {
                "eligible": False,
                "status": "MISSING",
                "handle": handle_id,
                "authority": "resolution only; ordinary admission remains required",
                "reason": "unknown_session_alias",
                "reference_kind": "session_alias",
            }
        result = super().resolve_point(
            self._aliases[handle_id], offset, observation, image, now_ns,
            session_scope=session_scope
        )
        result["handle"] = handle_id
        result["reference_kind"] = "session_alias"
        result["private_registry_id_exposed"] = False
        return result
