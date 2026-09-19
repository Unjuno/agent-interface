"""Product selector for promoted Agent Interface native backends."""

from .selector import BackendPlan, BackendUnavailable, open_session, select_backend, validate_targets

__all__ = ["BackendPlan", "BackendUnavailable", "open_session", "select_backend", "validate_targets"]
