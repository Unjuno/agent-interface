import map01_recovery_cover_mechanism_v3_runner as wrapper
import map01_recovery_cover_matched_v2_runner as base


def test_identity_patch():
    assert wrapper.ALLOCATION_ID == "map01-recovery-cover-mechanism-live-v3-01"
    assert wrapper.WORKFLOW_PATH == ".github/workflows/map01-recovery-cover-mechanism-live-v3-01.yml"
    wrapper.configure()
    assert base.ALLOCATION_ID == wrapper.ALLOCATION_ID
    assert base.EXPECTED_WORKFLOW_PATH == wrapper.WORKFLOW_PATH


def test_new_owner_accepts_and_old_owner_rejects():
    wrapper.configure()
    current = {
        "schema": "formal-allocation-global-owner-v1",
        "allocation_id": wrapper.ALLOCATION_ID,
        "workflow_path": wrapper.WORKFLOW_PATH,
        "required_branch": "main",
        "result_class": "PASS_CANONICAL_GLOBAL_OWNER",
        "may_enter_formal_step": True,
        "current_head_branch": "main",
        "owner_head_branch": "main",
        "matching_run_count": 1,
        "current_run_id": 10,
        "owner_run_id": 10,
    }
    base.validate_launch_owner(current)
    old = dict(current, allocation_id="map01-recovery-cover-matched-live-v2-01")
    try:
        base.validate_launch_owner(old)
    except ValueError as exc:
        assert "allocation_id" in str(exc)
    else:
        raise AssertionError("old allocation identity must be rejected")


if __name__ == "__main__":
    tests = [test_identity_patch, test_new_owner_accepts_and_old_owner_rejects]
    for test in tests:
        test()
    print(f"PASS {len(tests)} mechanism-v3 identity tests")
