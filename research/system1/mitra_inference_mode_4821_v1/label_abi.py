"""Deterministic class encoding and explicit probability-column mapping."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


def encode_labels(labels: Iterable[str], vocabulary: Sequence[str] | None = None):
    values = np.asarray(list(labels), dtype=object)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("labels must be a non-empty one-dimensional sequence")
    if any(not isinstance(value, str) or not value for value in values.tolist()):
        raise ValueError("labels must contain non-empty strings")
    observed = set(values.tolist())
    classes = tuple(sorted(observed)) if vocabulary is None else tuple(vocabulary)
    if not classes or len(classes) != len(set(classes)):
        raise ValueError("vocabulary must be non-empty and unique")
    if observed != set(classes):
        raise ValueError("observed labels must exactly match the frozen vocabulary")
    index = {label: class_id for class_id, label in enumerate(classes)}
    encoded = np.fromiter((index[value] for value in values.tolist()), dtype=np.int64, count=len(values))
    if encoded.dtype != np.int64 or set(np.unique(encoded).tolist()) != set(range(len(classes))):
        raise AssertionError("encoded labels are not contiguous int64 IDs")
    return encoded, classes


def restore_probability_columns(probabilities, column_class_ids, vocabulary):
    """Return columns in the explicit class-ID order established at fit time."""
    matrix = np.asarray(probabilities, dtype=np.float64)
    ids = tuple(int(value) for value in column_class_ids)
    expected = tuple(range(len(vocabulary)))
    if matrix.ndim != 2 or matrix.shape[1] != len(ids):
        raise ValueError("probability shape does not match explicit column IDs")
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("probability columns must bind every frozen class ID exactly once")
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError("probabilities must be finite and nonnegative")
    order = [ids.index(class_id) for class_id in expected]
    result = matrix[:, order]
    if not np.allclose(result.sum(axis=1), 1.0, atol=1e-4, rtol=0):
        raise ValueError("probability rows must sum to one")
    return result
