"""Translate a narrow structured Calc plan into registered task data.

This adapter is deliberately data-only. It does not reuse coordinates,
observations, aliases, session authority, or execution claims from a model
response. A caller must still make a fresh observation and pass the existing
Calc preparation, minting, and compiled execution gates.
"""
import math


_MIN_CONFIDENCE = 0.90
_MAX_NOTE_CHARS = 220
_EXPECTED_FIELDS = {
    "visible_sheet", "selected_cell", "cells_blank", "proposed_actions",
    "confidence", "visual_note",
}
_EXPECTED_ACTIONS = ["enter_731_in_A1", "enter_864_in_A2", "save"]


def adapt_calc_model_plan(answer):
    """Return fixed registered task values after strict plan-shape checks.

    ``confidence`` is only a rejection threshold for this historical fixture;
    it is not evidence of correctness or authorization. The runtime must
    independently observe the live target and verify the requested effects.
    """
    if type(answer) is not dict or set(answer) != _EXPECTED_FIELDS:
        raise ValueError("exact Calc model-plan fields required")
    confidence = answer["confidence"]
    try:
        finite_confidence = (type(confidence) in (int, float)
                             and math.isfinite(confidence))
    except OverflowError:
        finite_confidence = False
    if (not finite_confidence or confidence < _MIN_CONFIDENCE
            or confidence > 1):
        raise ValueError("Calc plan confidence is below the registered threshold")
    if answer["visible_sheet"] != "Sheet1":
        raise ValueError("expected worksheet is not identified")
    if answer["selected_cell"] != "A1":
        raise ValueError("expected starting cell is not identified")
    if answer["cells_blank"] is not True:
        raise ValueError("blank worksheet precondition is not met")
    if (type(answer["proposed_actions"]) is not list
            or answer["proposed_actions"] != _EXPECTED_ACTIONS):
        raise ValueError("Calc plan actions or order do not match the task")
    note = answer["visual_note"]
    if (type(note) is not str or len(note) > _MAX_NOTE_CHARS
            or any(ord(char) < 0x20 and char not in "\t\n\r" for char in note)):
        raise ValueError("Calc plan visual note is malformed")

    # These values come from the preregistered task contract, not parsed text.
    return {"A1": "731", "A2": "864"}
