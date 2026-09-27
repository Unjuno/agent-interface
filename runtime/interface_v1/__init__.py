"""Cross-platform Agent Interface discovery facade v1."""
from .doctor import report
from .native_probe import probe_native

__all__ = ["probe_native", "report"]
