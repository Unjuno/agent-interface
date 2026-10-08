import candidate


def test_coverage_only_control_drops_the_expensive_sentinel():
    result = candidate.run()
    assert result["coverage_negative_control_misses_release_loss"]
    assert result["coverage_only"]["cost"] == 1
    assert result["detection_aware"]["cost"] == 6


def test_detection_aware_retains_sentinels_and_known_faults():
    result = candidate.run()
    assert result["detection_subset_retains_all_mandatory"]
    assert result["detection_subset_retains_all_known_detectable"]


def test_unknown_and_equivalent_mutant_are_not_misreported_as_kills():
    result = candidate.run()
    assert result["unknown_preserved"]
    assert result["unknown_cell_count"] == 3
    assert result["equivalent_mutant_excluded"]
    assert not result["full"]["kills"]["unknown_fault"]


def test_same_capability_labels_do_not_imply_same_fault_discrimination():
    assert candidate.CAPABILITIES["cheap_a"] == candidate.CAPABILITIES["cheap_b"]
    assert candidate.KILLS["cheap_a"] != candidate.KILLS["cheap_b"]
