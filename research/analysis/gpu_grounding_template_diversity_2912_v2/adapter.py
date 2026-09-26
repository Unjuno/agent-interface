"""Map fixed-pool argmax cells to strict compiled-form-grounding-v1 points."""
from compiled_form_grounding_v1 import validate
from render import source_point


METHOD = {
    "first_action": "enter_exact_token",
    "continue_when": "field_pixels_changed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}


def candidate(field_cell, submit_cell):
    field = source_point(field_cell)
    submit = source_point(submit_cell)
    value = {
        "format": "compiled-form-grounding-v1",
        "field": {"point_space": "source_observation_pixels", "point": {"x": field[0], "y": field[1]},
                  "motion_model": "surface_origin_translation"},
        "submit": {"point_space": "source_observation_pixels", "point": {"x": submit[0], "y": submit[1]},
                   "motion_model": "surface_origin_translation"},
        "method": METHOD.copy(),
    }
    return value, validate(value)


def cell_to_point(logits):
    """Return renderer-grid [row,col] argmax and per-target confidence."""
    import torch
    if tuple(logits.shape) != (2, 8, 10):
        raise ValueError("expected two [8,10] target heatmaps")
    probs = torch.softmax(logits.flatten(1), dim=1)
    flat = probs.argmax(dim=1)
    cells = [[int(v.item()) // 10, int(v.item()) % 10] for v in flat]
    confidence = [float(probs[k, flat[k]].item()) for k in range(2)]
    return cells, confidence
