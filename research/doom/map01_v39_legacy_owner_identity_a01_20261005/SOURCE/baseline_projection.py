import hashlib

def input_edge_receipts(events):
    """Project legacy owner receipts and measured X-adapter edge brackets separately."""
    grouped = {}
    adapter_grouped = {}
    invalid = []
    for event in events:
        if type(event) is not dict:
            continue
        event_name = event.get("event")
        measurement = event.get("physical_key_measurement")
        adapter_edge = (measurement.get("adapter_edge")
                        if type(measurement) is dict else None)
        adapter_candidate = (
            event_name == "input_release_measurement" or
            (event_name == "input_admission" and type(measurement) is dict))
        if adapter_candidate:
            edge_name = adapter_edge.get("edge") if type(adapter_edge) is dict else None
            expected_edge = ("down" if event_name == "input_admission" else "up")
            identifier, step, key, token = (event.get("id"), event.get("step"),
                                            event.get("key"), event.get("intent_token"))
            if (type(identifier) is not str or not identifier or
                    type(step) is not int or step < 0 or
                    type(key) is not str or not key or
                    type(token) is not str or not token):
                invalid.append({
                    "status": "identity_unavailable",
                    "event": event_name,
                    "step": step if type(step) is int else None,
                    "key": key if type(key) is str else None,
                    "scope": "adapter edge bracket unpaired; source event identity incomplete",
                })
                continue
            actuation_id = (adapter_edge.get("actuation_id")
                            if type(adapter_edge) is dict else None)
            bucket = adapter_grouped.setdefault(
                (identifier, step, key, token, actuation_id),
                {"down": [], "up": []})
            # Outer event type and nested edge label are both part of the
            # receipt identity. Do not let one release event supply a press.
            bucket[expected_edge].append(event)
            continue
        if event_name not in ("input_admission", "input_release_transition"):
            continue
        identifier = event.get("id")
        step = event.get("step")
        key = event.get("key")
        token = event.get("intent_token")
        if (type(identifier) is not str or not identifier or
                type(step) is not int or step < 0 or
                type(key) is not str or not key or
                type(token) is not str or not token):
            invalid.append({
                "status": "identity_unavailable",
                "event": event["event"],
                "step": step if type(step) is int else None,
                "key": key if type(key) is str else None,
                "scope": "per-key timing unpaired; source event identity incomplete",
            })
            continue
        has_admission_position = "admission_position" in event
        admission_position = event.get("admission_position")
        if (has_admission_position and
                (type(admission_position) is not int or admission_position < 0)):
            invalid.append({
                "status": "identity_unavailable",
                "event": event["event"],
                "step": step,
                "key": key,
                "scope": "per-key timing unpaired; admission position is invalid",
            })
            continue
        group_key = (identifier, step, key, token, admission_position)
        bucket = grouped.setdefault(group_key, {"admission": [], "release": []})
        bucket["admission" if event["event"] == "input_admission" else "release"].append(event)

    receipts = list(invalid)
    for (identifier, step, key, token, actuation_id), bucket in adapter_grouped.items():
        downs, ups = bucket["down"], bucket["up"]
        down = downs[0] if len(downs) == 1 else None
        up = ups[0] if len(ups) == 1 else None

        def edge_of(row):
            data = row.get("physical_key_measurement") if row else None
            return data.get("adapter_edge") if type(data) is dict else None

        def valid_interval(value):
            return (type(value) is list and len(value) == 2 and
                    all(type(item) is int for item in value) and value[0] <= value[1])

        def bracket_matches(data, edge, edge_name, status):
            bracket = data.get("bracket") if type(data) is dict else None
            interval_name = ("physical_down_interval" if edge_name == "down"
                             else "physical_up_interval")
            return (
                type(bracket) is dict and type(edge) is dict and
                bracket.get("key") == edge.get("key") and
                bracket.get("owner_id") == edge.get("owner_id") and
                bracket.get("intent_token") == edge.get("intent_token") and
                bracket.get(interval_name) == edge.get("interval") and
                bracket.get("status") == status and
                bracket.get("grants_input_authority") is False and
                bracket.get("application_consumption_observed") is False)

        def admission_window_matches(row, data):
            pre = data.get("pre_sample") if type(data) is dict else None
            admitted_ns = row.get("admitted_ns") if type(row) is dict else None
            return (
                type(pre) is dict and type(admitted_ns) is int and
                type(pre.get("started_ns")) is int and
                admitted_ns <= pre["started_ns"])

        def sample_window_matches(data, row, edge_name):
            pre = data.get("pre_sample") if type(data) is dict else None
            post = data.get("post_sample") if type(data) is dict else None
            pre_down, post_down = (False, True) if edge_name == "down" else (True, False)

            def valid_sample(sample, expected_down):
                return (
                    type(sample) is dict and sample.get("available") is True and
                    sample.get("down") is expected_down and sample.get("error") is None and
                    type(sample.get("started_ns")) is int and
                    type(sample.get("finished_ns")) is int and
                    sample["started_ns"] <= sample["finished_ns"])

            request_name = "press_request_ns" if edge_name == "down" else "release_request_ns"
            request_ns = data.get(request_name) if type(data) is dict else None
            sync_ns = data.get("sync_return_ns") if type(data) is dict else None
            if (not valid_sample(pre, pre_down) or not valid_sample(post, post_down) or
                    type(request_ns) is not int or type(sync_ns) is not int or
                    pre["finished_ns"] > request_ns or request_ns > sync_ns or
                    sync_ns > post["started_ns"] or
                    edge_name == "down" and (type(row.get("input_ack_ns")) is not int or
                                                  row.get("input_ack_ns") != sync_ns) or
                    edge_name == "up" and data.get("release_attempted") is not True):
                return False
            bracket = data.get("bracket")
            interval_name = "physical_down_interval" if edge_name == "down" else "physical_up_interval"
            return (type(bracket) is dict and
                    bracket.get(interval_name) == [pre["finished_ns"], post["finished_ns"]])

        down_data = down.get("physical_key_measurement") if down else None
        up_data = up.get("physical_key_measurement") if up else None
        down_edge, up_edge = edge_of(down), edge_of(up)
        down_interval = down_edge.get("interval") if type(down_edge) is dict else None
        up_interval = up_edge.get("interval") if type(up_edge) is dict else None
        down_actuation = down_edge.get("actuation_id") if type(down_edge) is dict else None
        up_actuation = up_edge.get("actuation_id") if type(up_edge) is dict else None
        down_owner = down_edge.get("owner_id") if type(down_edge) is dict else None
        up_owner = up_edge.get("owner_id") if type(up_edge) is dict else None
        no_application_consumption_conflict = all(
            type(row) is dict and
            ("application_consumption_observed" not in row or
             row.get("application_consumption_observed") is False)
            for row in (
                down, up, down_data, up_data, down_edge, up_edge,
                down_data.get("bracket") if type(down_data) is dict else None,
                up_data.get("bracket") if type(up_data) is dict else None,
                down_data.get("pre_sample") if type(down_data) is dict else None,
                down_data.get("post_sample") if type(down_data) is dict else None,
                up_data.get("pre_sample") if type(up_data) is dict else None,
                up_data.get("post_sample") if type(up_data) is dict else None))
        complete = (
            len(downs) == 1 and len(ups) == 1 and
            type(down_data) is dict and type(up_data) is dict and
            type(down_edge) is dict and type(up_edge) is dict and
            down_edge.get("edge") == "down" and up_edge.get("edge") == "up" and
            down_data.get("edge") == "down" and up_data.get("edge") == "up" and
            down_data.get("classification") == "CONFIRMED_PHYSICAL_DOWN" and
            up_data.get("classification") == "CONFIRMED_PHYSICAL_UP" and
            down_data.get("identity_status") == "MINTED" and
            up_data.get("identity_status") == "RETIRED" and
            down_data.get("actuation_id") == down_edge.get("actuation_id") and
            up_data.get("actuation_id") == up_edge.get("actuation_id") and
            down_data.get("grants_input_authority") is False and
            up_data.get("grants_input_authority") is False and
            down_edge.get("status") == "CONFIRMED_PHYSICAL_DOWN" and
            up_edge.get("status") == "CONFIRMED_PHYSICAL_UP" and
            valid_interval(down_interval) and valid_interval(up_interval) and
            down_interval[1] < up_interval[0] and
            type(down_actuation) is str and bool(down_actuation) and
            down_actuation == up_actuation and
            type(down_owner) is str and bool(down_owner) and down_owner == up_owner and
            all(row.get("id") == identifier and row.get("step") == step and
                row.get("key") == key and row.get("intent_token") == token and
                row.get("owner_id") == down_owner and
                row.get("grants_input_authority",
                        row["physical_key_measurement"].get("grants_input_authority")) is False
                for row in (down, up)) and
            all(edge.get("key") == key and edge.get("intent_token") == token and
                edge.get("actuation_id") == down_actuation and
                edge.get("owner_id") == down_owner and
                edge.get("grants_input_authority") is False
                for edge in (down_edge, up_edge)) and
            down_data.get("application_consumption_observed") is False and
            up_data.get("application_consumption_observed") is False and
            no_application_consumption_conflict and
            bracket_matches(down_data, down_edge, "down", "CONFIRMED_PHYSICAL_DOWN") and
            bracket_matches(up_data, up_edge, "up", "CONFIRMED_PHYSICAL_UP") and
            admission_window_matches(down, down_data) and
            sample_window_matches(down_data, down, "down") and
            sample_window_matches(up_data, up, "up"))
        receipts.append({
            "status": "adapter_edge_brackets_paired" if complete else
                      "adapter_edge_receipt_incomplete",
            "program_id_sha256": hashlib.sha256(identifier.encode("utf-8")).hexdigest(),
            "intent_token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
            "owner_id_sha256": (hashlib.sha256(down_owner.encode("utf-8")).hexdigest()
                                if type(down_owner) is str else None),
            "actuation_id_sha256": (hashlib.sha256(actuation_id.encode("utf-8")).hexdigest()
                                    if type(actuation_id) is str else None),
            "step": step,
            "key": key,
            "input_admitted_ns": (down.get("admitted_ns") if complete else None),
            "down_press_request_ns": (down_data.get("press_request_ns")
                                      if complete else None),
            "down_sync_return_ns": (down_data.get("sync_return_ns")
                                    if complete else None),
            "down_edge_interval_ns": down_interval if complete else None,
            "up_release_request_ns": (up_data.get("release_request_ns")
                                      if complete else None),
            "up_sync_return_ns": (up_data.get("sync_return_ns")
                                  if complete else None),
            "up_edge_interval_ns": up_interval if complete else None,
            "grants_input_authority": False if complete else None,
            "application_consumption_observed": False if complete else None,
            "scope": ("InputOwner v12 X-server keymap sampling brackets; no application "
                      "receipt, physical dwell claim, or task-benefit claim"),
        })
    for (identifier, step, key, token, admission_position), bucket in grouped.items():
        admissions = bucket["admission"]
        releases = bucket["release"]
        admission = admissions[0] if len(admissions) == 1 else None
        release = releases[0] if len(releases) == 1 else None
        owner_v11 = release.get("owner_keyup_receipt") if release else None
        v11_contract = bool(release and (
            "owner_keyup_receipt" in release or "owner_keyup_join" in release))
        owner = (owner_v11 if v11_contract else
                 (release.get("owner_thread_keyup_receipt") if release else None))
        admitted_ns = admission.get("admitted_ns") if admission else None
        input_ack_ns = admission.get("input_ack_ns") if admission else None
        release_started_ns = release.get("release_call_started_ns") if release else None
        release_returned_ns = release.get("release_call_returned_ns") if release else None
        admission_owner_id = (admission.get("owner_id")
                              if type(admission) is dict else None)
        keyup_started_ns = (owner.get("owner_keyup_started_ns")
                            if v11_contract and type(owner) is dict else
                            (owner.get("owner_keyrelease_started_ns")
                             if type(owner) is dict else None))
        sync_returned_ns = owner.get("owner_sync_returned_ns") if type(owner) is dict else None
        if v11_contract:
            sync_completed = (type(owner) is dict and
                              owner.get("xsync_completed") is True and
                              owner.get("sync_error") is None)
            owner_history_complete = (
                release.get("owner_release_history_complete") is True and
                release.get("owner_cleanup_intervened") is False)
            owner_verified = (
                release.get("owner_keyup_join") == "MATCHED_EXPLICIT_KEYUP" and
                release.get("owner_transition_verified") is True and
                release.get("admission_identity_status") == "matched" and
                release.get("admission_position") == admission_position and
                release.get("ordinary_release_candidate") is True)
            owner_contract_valid = (
                type(owner) is dict and
                owner.get("event") == "owner_keyup" and
                owner.get("schema") == "owner-keyup-v11" and
                owner.get("reason") == "explicit_up" and
                owner.get("key") == key and owner.get("intent_token") == token and
                type(admission_owner_id) is str and bool(admission_owner_id) and
                release.get("owner_id") == admission_owner_id and
                owner.get("owner_id") == admission_owner_id and
                type(admission_position) is int and
                admission.get("admission_position") == admission_position and
                owner.get("physical_verification_authoritative") is False and
                owner.get("grants_input_authority") is False and
                release.get("physical_verification_authoritative") is False and
                release.get("grants_input_authority") is False)
        else:
            sync_completed = (type(owner) is dict and
                              owner.get("server_sync_completed") is True)
            owner_history_complete = (
                release.get("owner_thread_keyup_history_complete") is True
                if release else False)
            owner_verified = (release.get("owner_thread_keyup_verified") is True
                              if release else False)
            owner_contract_valid = (
                type(owner) is dict and owner.get("event") == "owner_explicit_keyup")

        if len(admissions) > 1 or len(releases) > 1:
            status = "ambiguous_input_edges"
        elif admission is None:
            status = "release_without_admission"
        elif release is None:
            status = "admission_without_release"
        elif (release.get("operation") != "up" or type(owner) is not dict or
              not owner_contract_valid or
              owner.get("key") != key or owner.get("intent_token") != token or
              not sync_completed or not owner_verified or
              not owner_history_complete or
              type(admitted_ns) is not int or type(input_ack_ns) is not int or
              input_ack_ns < admitted_ns or
              type(release_started_ns) is not int or type(release_returned_ns) is not int or
              type(keyup_started_ns) is not int or type(sync_returned_ns) is not int or
              keyup_started_ns < input_ack_ns or
              release_started_ns < input_ack_ns or
              keyup_started_ns < release_started_ns or
              sync_returned_ns < keyup_started_ns or
              release_returned_ns < sync_returned_ns):
            status = "release_receipt_incomplete"
        else:
            status = "paired"

        def delta_ms(start, end):
            if type(start) is int and type(end) is int and end >= start:
                return round((end - start) / 1_000_000, 6)
            return None

        receipts.append({
            "status": status,
            "program_id_sha256": hashlib.sha256(identifier.encode("utf-8")).hexdigest(),
            "intent_token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
            "step": step,
            "key": key,
            "admission_position": admission_position,
            "admitted_ns": admitted_ns if type(admitted_ns) is int else None,
            "input_ack_ns": input_ack_ns if type(input_ack_ns) is int else None,
            "release_call_started_ns": release_started_ns if type(release_started_ns) is int else None,
            "owner_keyrelease_started_ns": (keyup_started_ns
                                             if type(keyup_started_ns) is int else None),
            "owner_sync_returned_ns": (sync_returned_ns
                                        if type(sync_returned_ns) is int else None),
            "release_call_returned_ns": release_returned_ns if type(release_returned_ns) is int else None,
            "admitted_to_owner_keyup_start_ms": (delta_ms(admitted_ns, keyup_started_ns)
                                                  if status == "paired" else None),
            "input_ack_to_owner_keyup_start_ms": (delta_ms(input_ack_ns, keyup_started_ns)
                                                  if status == "paired" else None),
            "server_sync_completed": sync_completed,
            "owner_thread_keyup_verified": owner_verified,
            "owner_keyup_history_complete": owner_history_complete,
            "physical_verification_authoritative": (
                release.get("physical_verification_authoritative") is True
                if release else False),
            "scope": ("owner admission-to-keyup-request timing; server synchronization only, "
                      "not physical key-down duration or task benefit"),
        })
    return receipts
