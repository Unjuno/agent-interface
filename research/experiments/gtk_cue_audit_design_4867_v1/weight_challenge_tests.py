import hashlib
import numpy as np


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def validate_weight_binding(weights, expected_digest):
    return digest(weights) == expected_digest


def probability(frame, weight, bias=0.0):
    x = frame.astype(np.float32) / np.float32(255.0)
    z = float(np.clip(x @ weight + bias, -30.0, 30.0))
    return 1.0 / (1.0 + np.exp(-z))


def run_tests():
    frame = np.asarray([255], dtype=np.uint8)
    original = np.asarray([np.float32(0.25)], dtype=np.float32)
    expected = digest(original)
    assert validate_weight_binding(original, expected)

    tiny = original.copy()
    tiny[0] = np.nextafter(tiny[0], np.float32(np.inf), dtype=np.float32)
    assert tiny[0] != original[0]
    assert abs(probability(frame, tiny) - probability(frame, original)) <= 1e-6
    assert not validate_weight_binding(tiny, expected), "byte-exact binding must reject even in-tolerance mutation"

    large = original.copy()
    large[0] = np.float32(float(large[0]) + 2.0)
    assert abs(probability(frame, large) - probability(frame, original)) > 1e-6
    assert not validate_weight_binding(large, expected)

    # Hash must bind shape/dtype as well as numeric values; canonicalize them explicitly.
    different_dtype = original.astype(np.float64)
    assert digest(different_dtype) != expected
    print({"original_hash": expected, "tiny_hash_rejected": True,
           "tiny_probability_delta": abs(probability(frame, tiny) - probability(frame, original)),
           "large_hash_rejected": True,
           "large_probability_delta": abs(probability(frame, large) - probability(frame, original)),
           "dtype_change_rejected": True})


if __name__ == "__main__":
    run_tests()
