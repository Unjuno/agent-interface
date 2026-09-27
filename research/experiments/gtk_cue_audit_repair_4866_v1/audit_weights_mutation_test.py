import numpy as np


def mutate_weight(weights):
    original = np.float32(weights[0, 0])
    changed = np.nextafter(original, np.float32(np.inf), dtype=np.float32)
    assert changed != original, "corruption mutation must change the stored float32 value"
    result = weights.copy()
    result[0, 0] = changed
    assert result[0, 0] != weights[0, 0], "corruption must survive assignment"
    return result


def main():
    values = np.asarray([[np.float32(-0.09448759)]], dtype=np.float32)
    mutated = mutate_weight(values)
    if np.array_equal(values, mutated):
        raise SystemExit("mutation control did not alter the array")
    print({"original": float(values[0, 0]), "changed": float(mutated[0, 0]),
           "changed_in_storage": True})


if __name__ == "__main__":
    main()
