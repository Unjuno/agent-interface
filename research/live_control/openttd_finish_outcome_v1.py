"""Classify an OpenTTD finish score without turning task failure into an assertion."""


def classify(path_name, evaluation, *, exit_code, proposals_executed, journal_calls, reason, arm):
    common = {
        "exit_code": exit_code,
        "arm": arm,
        "proposals_executed": proposals_executed,
        "journal_calls": journal_calls,
    }
    if path_name == "abort.json" or evaluation["success"] is not True:
        return "failure-evaluation.json", {
            **common,
            "reason": reason,
            "evaluation": evaluation,
            "success": False,
            "failure_mode": (
                "bounded_turn_limit"
                if path_name == "abort.json"
                else "visual_verify_false_positive"
            ),
        }
    return "result.json", {
        **common,
        "scope": "matched model-route proposal passed through isolated OpenTTD supervisor",
    }
