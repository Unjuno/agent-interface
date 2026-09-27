import hashlib
import numpy as np


def weight_digest(weights):
    contiguous = np.ascontiguousarray(weights)
    header = f"dtype={contiguous.dtype.str};shape={contiguous.shape};".encode("ascii")
    return hashlib.sha256(header + contiguous.tobytes()).hexdigest()


def probability(frame, weights, bias=0.0):
    x = frame.astype(np.float32) / np.float32(255.0)
    z = float(np.clip(x @ weights + bias, -30.0, 30.0))
    return 1.0 / (1.0 + np.exp(-z))


def run():
    frame = np.asarray([255], dtype=np.uint8)
    original = np.asarray([np.float32(.25)], dtype=np.float32)
    expected = weight_digest(original)
    assert weight_digest(original) == expected
    adjacent = original.copy()
    adjacent[0] = np.nextafter(adjacent[0], np.float32(np.inf), dtype=np.float32)
    tiny_delta = abs(probability(frame, adjacent) - probability(frame, original))
    assert tiny_delta <= 1e-6
    assert weight_digest(adjacent) != expected
    large = original.copy()
    large[0] = np.float32(float(large[0]) + 2.0)
    assert abs(probability(frame, large) - probability(frame, original)) > 1e-6
    assert weight_digest(large) != expected
    assert weight_digest(original.astype(np.float64)) != expected
    assert weight_digest(original.reshape(1, 1)) != expected
    print({"pass": True, "tiny_delta": tiny_delta,
           "large_delta": abs(probability(frame, large) - probability(frame, original)),
           "dtype_and_shape_bound": True})

if __name__ == "__main__": run()
