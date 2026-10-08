"""Finite synthetic episodes for Issue #6655; no external state or effects."""

BASE_MAIN_SHA = "9a573b00dc595e64d09387e567c85e10b61a46c1"
SEEDS = tuple(range(1, 33))

CASES = (
    {
        "case_id": "helpful_incidental_view",
        "baseline": {"view": "default"},
        "delta": {"view": "target_focused"},
        "classification": "incidental",
        "task": {"id": "locate_target", "required_view": "target_focused"},
        "eligible": True,
    },
    {
        "case_id": "harmful_stale_filter",
        "baseline": {"filter": "all"},
        "delta": {"filter": "stale_hides_required_cue"},
        "classification": "incidental",
        "task": {"id": "find_required_cue", "required_view": "cue_visible"},
        "eligible": True,
    },
    {
        "case_id": "irrelevant_theme",
        "baseline": {"theme": "neutral"},
        "delta": {"theme": "blue"},
        "classification": "incidental",
        "task": {"id": "read_value", "required_view": "value_visible"},
        "eligible": True,
    },
    {
        "case_id": "required_saved_effect",
        "baseline": {"saved_record": False},
        "delta": {"saved_record": True},
        "classification": "required_effect",
        "task": {"id": "continue_after_save", "required_effect": {"saved_record": True}},
        "eligible": True,
    },
    {
        "case_id": "incomplete_restoration",
        "baseline": {"panel": "closed"},
        "delta": {"panel": "stale_open"},
        "classification": "incidental",
        "task": {"id": "inspect_panel", "required_view": "panel_state_known"},
        "eligible": False,
        "exclusion_reason": "RESTORE_INCOMPLETE",
    },
    {
        "case_id": "shared_external_state",
        "baseline": {"shared_preference": "unknown"},
        "delta": {"shared_preference": "changed_elsewhere"},
        "classification": "shared_external",
        "task": {"id": "inspect_preference", "required_view": "preference_known"},
        "eligible": False,
        "exclusion_reason": "SHARED_STATE_UNOWNED",
    },
    {
        "case_id": "task_seed_mismatch",
        "baseline": {"view": "default"},
        "delta": {"view": "target_focused"},
        "classification": "incidental",
        "task": {"id": "locate_target", "required_view": "target_focused"},
        "eligible": False,
        "exclusion_reason": "TASK_SEED_MISMATCH",
        "reset_seed_offset": 1,
    },
)
