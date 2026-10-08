"""CPU construction regression for allocation-03's unsafe-admission control."""
def inject_unsafe_admission(result):
    values = result["raw_pairs"]["1024"][0]["cuda_admitted"]
    index = next((i for i, value in enumerate(values) if value == 0), None)
    if index is None:
        raise ValueError("no safe admission value to corrupt")
    before = values[index]
    values[index] = 1
    if values[index] == before:
        raise AssertionError("unsafe_admission mutation was a no-op")
    return index

def test_selects_and_flips_first_zero():
    result = {"raw_pairs": {"1024": [{"cuda_admitted": [1, 0, 0]}]}}
    assert inject_unsafe_admission(result) == 1
    assert result["raw_pairs"]["1024"][0]["cuda_admitted"] == [1, 1, 0]

def test_selects_zero_before_later_zero():
    result = {"raw_pairs": {"1024": [{"cuda_admitted": [0, 1]}]}}
    assert inject_unsafe_admission(result) == 0
    assert result["raw_pairs"]["1024"][0]["cuda_admitted"] == [1, 1]

def test_fails_closed_when_no_zero_exists():
    result = {"raw_pairs": {"1024": [{"cuda_admitted": [1, 1]}]}}
    try:
        inject_unsafe_admission(result)
    except ValueError:
        return
    raise AssertionError("all-one fixture should fail closed")

if __name__ == "__main__":
    for test in (test_selects_and_flips_first_zero, test_selects_zero_before_later_zero,
                 test_fails_closed_when_no_zero_exists):
        test()
    print("PASS 3/3: mutation flips a zero; no safe value fails closed")
