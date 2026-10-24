"""Join one provider-generation boundary to sequential public MCP calls.

This research adapter records exactly the callable and Relay bytes supplied by
its caller. A provider adapter may still hide internal retries; the journal
must not be treated as exhaustive until reconciled with independent provider
logs.
"""

import json


def _json_bytes(value):
    return json.dumps(value, allow_nan=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8")


class RecordedPublicMcpCaller:
    """Durably record provider attempts and their standard public Relay calls."""

    def __init__(self, relay, recorder):
        if not callable(getattr(relay, "request", None)):
            raise TypeError("relay must expose async request(bytes)")
        if not callable(getattr(recorder, "invoke_async", None)) or not callable(
                getattr(recorder, "invoke_tool_async", None)):
            raise TypeError("recorder must expose async provider and MCP boundaries")
        self.relay = relay
        self.recorder = recorder

    async def invoke_provider(self, attempt_id, request_bytes, provider_call):
        """Record one injected provider call before invoking it."""
        return await self.recorder.invoke_async(
            attempt_id, request_bytes, provider_call)

    async def invoke_generation_to_tool(self, attempt_id, request_bytes,
                                       provider_call, call_id, method,
                                       prepare_arguments):
        """Run one provider generation, then conditionally submit its tool call.

        ``prepare_arguments`` receives the full generation record only after
        its provider terminal record is durable. A non-completed attempt or
        missing response bytes is retained
        without submitting a tool call. This sequences the supplied outer
        provider invocation; it does not enumerate hidden provider retries.
        """
        generation = await self.invoke_provider(
            attempt_id, request_bytes, provider_call)
        if (not isinstance(generation, dict) or
                generation.get("status") != "completed" or
                not isinstance(generation.get("response_bytes"), bytes)):
            return {"generation": generation, "tool_response": None,
                    "tool_call_submitted": False}
        arguments = prepare_arguments(generation)
        if not isinstance(arguments, dict):
            raise TypeError("prepared public MCP arguments must be an object")
        response = await self.call_tool(
            attempt_id, call_id, method, arguments)
        return {"generation": generation, "tool_response": response,
                "tool_call_submitted": True}

    async def invoke_generation_to_tool_with_one_safe_recovery(
            self, attempt_id, request_bytes, provider_call, call_id, method,
            prepare_arguments, recover):
        """Allow one fresh plan after a refusal and an explicit target review.

        ``recover`` performs the public review, mints a new target from that
        review, and returns its receipt with one provider/MCP attempt. Eligibility
        requires explicit no-dispatch evidence, zero transitions, and an owner
        snapshot with no tracked input obligations or pending input recovery.
        This is not a physical-neutrality/release verdict. The review invalidates
        old aliases and binds the new plan to a fresh source. The second
        generation is terminal for this call; this method never loops.
        """
        initial = await self.invoke_generation_to_tool(
            attempt_id, request_bytes, provider_call, call_id, method,
            prepare_arguments)
        if not self._has_recoverable_preinput_refusal(initial):
            return {"initial": initial, "recovery": None,
                    "review": None, "recovery_started": False}

        plan = await recover(initial)
        required = {"attempt_id", "request_bytes", "provider_call", "call_id",
                    "method", "prepare_arguments", "review_response",
                    "target_response"}
        if type(plan) is not dict or set(plan) != required:
            raise TypeError(
                "recovery plan must contain one attempt, review, and target receipt")
        if (plan["attempt_id"] == attempt_id or
                plan["call_id"] == call_id):
            raise ValueError("recovery must use new attempt and call ids")
        if not self._valid_fresh_review(initial, plan["review_response"]):
            return {"initial": initial, "recovery": None,
                    "review": plan["review_response"],
                    "recovery_started": False}
        prior_aliases = self._prior_target_aliases(initial)
        if (prior_aliases is None or not self._valid_fresh_target(
                plan["review_response"], plan["target_response"], prior_aliases)):
            return {"initial": initial, "recovery": None,
                    "review": plan["review_response"],
                    "recovery_started": False}

        def prepare_reviewed_arguments(generation):
            arguments = plan["prepare_arguments"](generation)
            if not self._arguments_bind_fresh_target(
                    arguments, plan["review_response"], plan["target_response"],
                    prior_aliases):
                raise ValueError(
                    "replanned tool arguments do not bind the reviewed target")
            return arguments

        recovery = await self.invoke_generation_to_tool(
            plan["attempt_id"], plan["request_bytes"], plan["provider_call"],
            plan["call_id"], plan["method"], prepare_reviewed_arguments)
        return {"initial": initial, "review": plan["review_response"],
                "recovery": recovery,
                "recovery_started": True}

    @staticmethod
    def _tool_body(response, expected_method=None):
        if (type(response) is not dict or response.get("status") != "returned" or
                (expected_method is not None and
                 response.get("tool") != expected_method)):
            return None
        envelope = response.get("result")
        content = envelope.get("content") if type(envelope) is dict else None
        if type(content) is not list:
            return None
        text_rows = [item.get("text") for item in content
                     if type(item) is dict and type(item.get("text")) is str]
        if len(text_rows) != 1:
            return None
        try:
            body = json.loads(text_rows[0])
        except (TypeError, ValueError):
            return None
        return body if type(body) is dict else None

    @classmethod
    def _has_recoverable_preinput_refusal(cls, result):
        if type(result) is not dict or not result.get("tool_call_submitted"):
            return False
        body = cls._tool_body(result.get("tool_response"),
                              "interface_guarded_compiled")
        receipt = body.get("method_receipt") if body is not None else None
        if (type(receipt) is not dict or
                receipt.get("outcome") != "SAFE_YIELD" or
                receipt.get("completed_transitions") != 0):
            return False
        events = receipt.get("critical_events")
        if type(events) is not list:
            return False
        terminals = [event for event in events
                     if type(event) is dict and event.get("event") == "action_terminal"]
        admissions = [event for event in events
                      if type(event) is dict and
                      event.get("event") == "admission_refused"]
        no_dispatch_refusal = (
            receipt.get("reason") == "execution_refused" and
            len(terminals) == 1 and terminals[0].get("status") == "refused" and
            terminals[0].get("input_dispatched") is False)
        association_refusal = (
            receipt.get("reason") == "association_changed" and
            len(admissions) == 1 and
            admissions[0].get("status") == "association_changed" and
            not terminals)
        session = body.get("session")
        owner = session.get("owner_process") if type(session) is dict else None
        obligations = (session.get("owner_input_obligations")
                       if type(session) is dict else None)
        return ((no_dispatch_refusal or association_refusal) and
                type(session) is dict and
                session.get("recovery_required") is False and
                session.get("owner_input_obligations_source") == "child_rpc_snapshot" and
                type(obligations) is dict and obligations.get("keys") == {} and
                obligations.get("buttons") == [] and
                type(owner) is dict and owner.get("alive") is True and
                owner.get("retired") is False)

    @classmethod
    def _valid_fresh_review(cls, initial, review_response):
        refusal = cls._tool_body(
            initial.get("tool_response") if type(initial) is dict else None,
            "interface_guarded_compiled")
        review = cls._tool_body(review_response,
                                "interface_guarded_review_window")
        if refusal is None or review is None:
            return False
        old_session = refusal.get("session")
        new_session = review.get("session")
        old_owner = old_session.get("owner_process") if type(old_session) is dict else None
        new_owner = new_session.get("owner_process") if type(new_session) is dict else None
        source = review.get("source")
        old_receipt = refusal.get("method_receipt")
        observations = old_receipt.get("observations") if type(old_receipt) is dict else None
        prior_sequences = ([row.get("sequence") for row in observations
                            if type(row) is dict and type(row.get("sequence")) is int]
                           if type(observations) is list else [])
        if type(old_session) is dict and type(old_session.get("observation_sequence")) is int:
            prior_sequences.append(old_session["observation_sequence"])
        binding = (source.get("pointer_binding") if type(source) is dict else None)
        generation = (binding.get("process_generation") if type(binding) is dict else None)
        obligations = (new_session.get("owner_input_obligations")
                       if type(new_session) is dict else None)
        return (review.get("status") == "reviewed" and
                review.get("input_dispatched") is False and
                type(source) is dict and type(source.get("sequence")) is int and
                bool(prior_sequences) and source["sequence"] > max(prior_sequences) and
                type(generation) is str and len(generation) == 64 and
                all(char in "0123456789abcdef" for char in generation) and
                type(old_owner) is dict and type(new_owner) is dict and
                type(old_owner.get("pid")) is int and old_owner.get("alive") is True and
                new_owner.get("pid") == old_owner["pid"] and
                new_owner.get("alive") is True and new_owner.get("retired") is False and
                type(new_session) is dict and new_session.get("review_required") is False and
                new_session.get("recovery_required") is False and
                new_session.get("owner_input_obligations_source") == "child_rpc_snapshot" and
                type(obligations) is dict and obligations.get("keys") == {} and
                obligations.get("buttons") == [] and
                type(new_session.get("compiled_scope")) is str and
                type(new_session.get("compiled_surface")) is str)

    @classmethod
    def _prior_target_aliases(cls, initial):
        generation = initial.get("generation") if type(initial) is dict else None
        response_bytes = (generation.get("response_bytes")
                          if type(generation) is dict else None)
        if type(response_bytes) is not bytes:
            return None
        try:
            payload = json.loads(response_bytes)
        except (TypeError, ValueError):
            return None
        interface = payload.get("interface") if type(payload) is dict else None
        symbols = interface.get("symbols") if type(interface) is dict else None
        if type(symbols) is not dict:
            return None
        aliases = {symbol.get("target_reference") for symbol in symbols.values()
                   if type(symbol) is dict and
                   type(symbol.get("target_reference")) is str}
        return aliases or None

    @classmethod
    def _valid_fresh_target(cls, review_response, target_response, prior_aliases):
        review = cls._tool_body(review_response,
                                "interface_guarded_review_window")
        target = cls._tool_body(target_response, "interface_guarded_mint")
        if review is None or target is None:
            return False
        source = review.get("source")
        review_session = review.get("session")
        target_session = target.get("session")
        review_owner = (review_session.get("owner_process")
                        if type(review_session) is dict else None)
        target_owner = (target_session.get("owner_process")
                        if type(target_session) is dict else None)
        target_obligations = (target_session.get("owner_input_obligations")
                              if type(target_session) is dict else None)
        offset = target.get("offset")
        return (review.get("status") == "reviewed" and
                type(source) is dict and type(source.get("sequence")) is int and
                target.get("status") == "minted" and
                target.get("input_dispatched") is False and
                target.get("source_sequence") == source["sequence"] and
                type(target.get("alias")) is str and
                target["alias"] not in prior_aliases and
                type(offset) is list and len(offset) == 2 and
                all(type(value) is int for value in offset) and
                type(review_session) is dict and type(target_session) is dict and
                target_session.get("compiled_scope") ==
                review_session.get("compiled_scope") and
                target_session.get("compiled_surface") ==
                review_session.get("compiled_surface") and
                target_session.get("review_required") is False and
                target_session.get("recovery_required") is False and
                target_session.get("owner_input_obligations_source") ==
                "child_rpc_snapshot" and
                type(target_obligations) is dict and
                target_obligations.get("keys") == {} and
                target_obligations.get("buttons") == [] and
                type(review_owner) is dict and type(target_owner) is dict and
                target_owner.get("pid") == review_owner.get("pid") and
                review_owner.get("alive") is True and
                target_owner.get("alive") is True and
                target_owner.get("retired") is False)

    @classmethod
    def _arguments_bind_fresh_target(cls, arguments, review_response,
                                     target_response, prior_aliases):
        if not cls._valid_fresh_target(
                review_response, target_response, prior_aliases):
            return False
        review = cls._tool_body(review_response,
                                "interface_guarded_review_window")
        target = cls._tool_body(target_response, "interface_guarded_mint")
        interface = arguments.get("interface") if type(arguments) is dict else None
        if type(interface) is not dict:
            return False
        review_session = review.get("session")
        if (interface.get("session_scope") != review_session.get("compiled_scope") or
                interface.get("surface") != review_session.get("compiled_surface")):
            return False
        symbols = interface.get("symbols")
        actions = interface.get("actions")
        bindings = arguments.get("bindings")
        if (type(symbols) is not dict or type(actions) is not dict or
                type(bindings) is not dict):
            return False
        if any(type(symbol) is dict and
               symbol.get("target_reference") in prior_aliases
               for symbol in symbols.values()):
            return False
        alias = target["alias"]
        offset = target["offset"]
        return any(
            type(action) is dict and
            type(symbols.get(action.get("target_symbol"))) is dict and
            symbols[action["target_symbol"]].get("target_reference") == alias and
            type(bindings.get(action_name)) is dict and
            bindings[action_name].get("offset") == offset
            for action_name, action in actions.items())

    async def call_tool(self, attempt_id, call_id, method, arguments):
        """Record the exact JSON request/response envelopes around Relay.request."""
        request = {"id": self.relay.next_id, "tool": method,
                   "arguments": arguments}
        request_bytes = _json_bytes(request)

        async def transport():
            response = await self.relay.request(request_bytes)
            return {"result": response, "response_bytes": _json_bytes(response)}

        return await self.recorder.invoke_tool_async(
            attempt_id, call_id, method, request_bytes, transport)
