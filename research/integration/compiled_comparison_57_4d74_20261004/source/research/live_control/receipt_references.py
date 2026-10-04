"""Compatibility imports for shared lossless receipt projections."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.cli_v1.receipt_references import (
    NATIVE_REFS, NATIVE_MULTI_REFS, compact_receipt, expand_receipt,
    compact_native_receipt, expand_native_receipt,
)
