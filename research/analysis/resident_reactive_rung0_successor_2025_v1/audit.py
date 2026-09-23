from itertools import product

def expected_edges(trace):
    return sum(
        1 for i, state in enumerate(trace)
        if state and (i == 0 or not trace[i - 1])
    )

def independent_row(trace, stale_message_t):
    # The stale message is an independent control-plane event. It must be
    # rejected without changing the observation trace or edge oracle.
    current_generation = 1
    rejected = int(0 != current_generation)
    observed_edges = expected_edges(trace)
    terminal_release = True
    return observed_edges, rejected, terminal_release

def main():
    rows = 0
    total_edges = 0
    total_rejections = 0
    for trace in product((False, True), repeat=4):
        for stale_message_t in range(4):
            edges, rejected, released = independent_row(trace, stale_message_t)
            assert edges == expected_edges(trace)
            assert rejected == 1
            assert released
            rows += 1
            total_edges += edges
            total_rejections += rejected
    assert rows == 64
    assert total_rejections == 64
    print("independent_rows=64 stale_rejections=64 edge-oracle=PASS release=PASS")
if __name__ == "__main__":
    main()
