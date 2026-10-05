"""Independent host audit joining target-dispatch captures to raw task events."""

from __future__ import annotations

ARMS = ("plain", "ephemeral", "persistent")
TASKS = ("A1", "A2", "A3", "B1", "B2", "B3")
TARGETS = ("palette_point", "target_point")


class DispatchAuditError(ValueError):
    pass


def audit(raw: dict, capture: dict) -> dict:
    if type(capture) is not dict or set(capture) != {"schema", "arms"}:
        raise DispatchAuditError("exact dispatch capture required")
    if capture["schema"] != "mindustry_target_dispatch_capture_v1":
        raise DispatchAuditError("unsupported dispatch capture schema")
    if type(raw) is not dict or type(raw.get("arms")) is not dict:
        raise DispatchAuditError("raw allocation arms required")
    if set(raw["arms"]) != set(ARMS) or set(capture["arms"]) != set(ARMS):
        raise DispatchAuditError("exact three-arm coverage required")

    checked = 0
    for arm in ARMS:
        raw_tasks, captured_tasks = raw["arms"][arm], capture["arms"][arm]
        if (type(raw_tasks) is not list or type(captured_tasks) is not list
                or len(raw_tasks) != len(TASKS) or len(captured_tasks) != len(TASKS)):
            raise DispatchAuditError("exact six-task coverage required")
        for index, (task_id, task, captured) in enumerate(
                zip(TASKS, raw_tasks, captured_tasks)):
            if (type(task) is not dict or type(captured) is not dict
                    or captured.get("task_id") != task_id):
                raise DispatchAuditError("dispatch task order mismatch")
            route = captured.get("route_record")
            model_calls = task.get("model_call_events")
            if (type(route) is not dict or route.get("task_id") != task_id
                    or route.get("layout") != task.get("layout")
                    or route.get("route") != task.get("route")
                    or type(model_calls) is not list
                    or route.get("model_calls") != len(model_calls)):
                raise DispatchAuditError("dispatch route does not match raw task")

            source = captured.get("source_sequence")
            source_observation = captured.get("source_observation")
            observations = task.get("observation_events")
            if (type(source) is not int or type(source_observation) is not dict
                    or source_observation.get("sequence") != source
                    or type(observations) is not list
                    or any(type(row) is not dict for row in observations)
                    or not any(row.get("sequence") == source for row in observations)):
                raise DispatchAuditError("source observation sequence is not in raw task")

            results = captured.get("target_results")
            dispatch_observations = captured.get("dispatch_observations")
            if (type(results) is not list or len(results) != 2
                    or type(dispatch_observations) is not list
                    or len(dispatch_observations) != 2
                    or any(type(row) is not dict for row in dispatch_observations)):
                raise DispatchAuditError("two target observations and results required")
            expected_attempts = []
            for target, result, observation in zip(TARGETS, results,
                                                   dispatch_observations):
                if type(result) is not dict or result.get("target") != target:
                    raise DispatchAuditError("target dispatch order mismatch")
                request, locator = result.get("request"), result.get("locator")
                if type(request) is not dict or type(locator) is not dict:
                    raise DispatchAuditError("compiled request and locator required")
                sequence = locator.get("validated_sequence")
                if (request.get("id") != f"{task_id}-{target}"
                        or request.get("target") != target
                        or request.get("expected_sequence") != sequence
                        or type(locator.get("source_sequence")) is not int
                        or locator["source_sequence"] > source
                        or type(sequence) is not int or sequence <= source
                        or observation.get("sequence") != sequence
                        or not any(row.get("sequence") == sequence
                                   for row in observations)):
                    raise DispatchAuditError("request is not bound to a fresh raw observation")
                if result.get("execution_receipt") != {
                        "request_id": request["id"], "terminal": True, "released": True}:
                    raise DispatchAuditError("terminal released receipt must bind request")
                expected_attempts.append(f"{arm}-{task_id}-{target}")

            inputs = task.get("input_events")
            if type(inputs) is not list or any(type(row) is not dict for row in inputs):
                raise DispatchAuditError("raw input events required")
            admissions = [row for row in inputs if row.get("status") == "ADMITTED"]
            if ([row.get("attempt_id") for row in admissions] != expected_attempts
                    or any(row.get("old_reference") is not False for row in admissions)):
                raise DispatchAuditError("raw admissions differ from ordered targets")
            feedback = task.get("input_feedback_events")
            if (type(feedback) is not list or any(type(row) is not dict for row in feedback)
                    or len(feedback) != 2
                    or [row.get("attempt_id") for row in task["input_feedback_events"]]
                       != expected_attempts):
                raise DispatchAuditError("each target must have matching feedback")
            releases = task.get("release_events", [])
            if (type(releases) is not list
                    or any(type(row) is not dict for row in releases)
                    or [row.get("attempt_id") for row in releases] != expected_attempts
                    or any(row.get("button_up") is not True
                           or row.get("keys_empty") is not True for row in releases)):
                raise DispatchAuditError("each target must have ordered verified release")

            persistent_b1 = arm == "persistent" and index == 3
            refused = [row for row in inputs if row.get("status") == "REFUSED"]
            if persistent_b1:
                old_sequence = captured.get("old_reference_sequence")
                repairs = task.get("repair_events")
                if (route.get("old_reference_status") != "stale"
                        or route.get("old_reference_pointer_admissions") != 0
                        or type(old_sequence) is not int or old_sequence >= source
                        or len(refused) != 1 or refused[0].get("old_reference") is not True
                        or type(repairs) is not list or len(repairs) != 1
                        or type(repairs[0]) is not dict
                        or repairs[0].get("old_reference_sequence") != old_sequence
                        or repairs[0].get("observed_sequence") != source):
                    raise DispatchAuditError("persistent B1 stale refusal/repair mismatch")
            elif refused:
                raise DispatchAuditError("old-reference refusal outside persistent B1")
            checked += 1
    return {"audit": "PASS_SYNTHETIC_DISPATCH_JOIN", "tasks_verified": checked,
            "target_dispatches_verified": checked * len(TARGETS)}
