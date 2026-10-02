"""Hand-authored positive and null controls for Issue #5927's proposed T0."""


def positive_case():
    return {
        "id": "save-modal-positive",
        "worlds": [
            {"id": "persisted", "safe_progress_actions": ["claim_complete"], "oracle_safe_progress_actions": ["claim_complete"]},
            {"id": "blocked", "safe_progress_actions": ["continue_recovery"], "oracle_safe_progress_actions": ["continue_recovery"]},
        ],
        "channels": [
            {"id": "dispatch_receipt", "declared": True, "fresh": True, "values": {"persisted": "dispatched", "blocked": "dispatched"}},
            {"id": "pixel_view", "declared": True, "fresh": True, "values": {"persisted": "same_pre_save_view", "blocked": "same_pre_save_view"}},
            {"id": "persistence_receipt", "declared": True, "fresh": True, "values": {"persisted": "saved", "blocked": "blocked"}},
        ],
    }


def null_case():
    return {
        "id": "shared-safe-inspect-null",
        "worlds": [
            {"id": "persisted", "safe_progress_actions": ["claim_complete", "inspect_again"], "oracle_safe_progress_actions": ["claim_complete", "inspect_again"]},
            {"id": "blocked", "safe_progress_actions": ["continue_recovery", "inspect_again"], "oracle_safe_progress_actions": ["continue_recovery", "inspect_again"]},
        ],
        "channels": [
            {"id": "persistence_receipt", "declared": True, "fresh": True, "values": {"persisted": "saved", "blocked": "blocked"}},
        ],
    }


def all_cases():
    return {"schema": "feedback-necessity-cases-v1", "cases": [positive_case(), null_case()]}
