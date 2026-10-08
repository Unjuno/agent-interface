import numpy as np


def probability(frame, weight, bias):
    x = frame.reshape(-1).astype(np.float32) / np.float32(255.0)
    z = float(np.clip(x @ weight + bias, -30.0, 30.0))
    return 1.0 / (1.0 + np.exp(-z))


def main():
    # Synthetic only: a one-dimensional pixel feature, no retained formal inputs.
    frame = np.asarray([255], dtype=np.uint8)
    weight = np.asarray([0.25], dtype=np.float32)
    bias = np.float32(0.0)
    original = probability(frame, weight, bias)

    adjacent = weight.copy()
    adjacent[0] = np.nextafter(adjacent[0], np.float32(np.inf), dtype=np.float32)
    adjacent_probability = probability(frame, adjacent, bias)
    tiny_delta = abs(adjacent_probability - original)
    tiny_within_tolerance = tiny_delta <= 1e-6

    substantial = weight.copy()
    substantial[0] += np.float32(2.0)
    substantial_probability = probability(frame, substantial, bias)
    substantial_delta = abs(substantial_probability - original)
    large_exceeds_tolerance = substantial_delta > 1e-6
    if not (tiny_within_tolerance and large_exceeds_tolerance):
        raise SystemExit("synthetic mutation boundary assumptions failed")

    print({"original_probability": original,
           "adjacent_float32_probability": adjacent_probability,
           "adjacent_delta": tiny_delta,
           "adjacent_accepted_by_1e-6_tolerance": tiny_within_tolerance,
           "large_mutation_probability": substantial_probability,
           "large_delta": substantial_delta,
           "large_mutation_exceeds_1e-6": large_exceeds_tolerance,
           "note": "synthetic behavior only; no formal evidence audited"})


if __name__ == "__main__":
    main()
