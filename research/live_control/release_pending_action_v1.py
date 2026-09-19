"""Client state for physical release now and program terminal later."""
import copy


class PendingAction:
    def __init__(self, action_id):
        self.action_id = action_id; self.accepted = None
        self.released = None; self.terminal = None; self.uncertainty = None

    def ingest(self, reply):
        try:
            if reply.get("status") != "boundary" or not isinstance(reply.get("records"), list):
                raise ValueError("resolved contiguous reply required")
            for row in reply["records"]:
                if row.get("id") != self.action_id: continue
                if row.get("event") == "accepted":
                    if self.accepted is not None: raise ValueError("duplicate acceptance")
                    if not isinstance(row.get("intent_token"), str): raise ValueError("intent token required")
                    self.accepted = copy.deepcopy(row)
                elif row.get("event") == "input_released":
                    release = row.get("owner_release")
                    if self.accepted is None or self.released is not None:
                        raise ValueError("unique release after acceptance required")
                    if (row.get("intent_token") != self.accepted["intent_token"] or
                            row.get("program_terminal_pending") is not True or
                            row.get("grants_input_authority") is not False or
                            not isinstance(release, dict) or release.get("verified") is not True or
                            release.get("keys_down") != [] or release.get("buttons_down") != []):
                        raise ValueError("verified token-bound empty release required")
                    self.released = copy.deepcopy(row)
                elif row.get("event") == "terminal":
                    if self.accepted is None or self.terminal is not None:
                        raise ValueError("unique terminal after acceptance required")
                    if self.released is not None:
                        interruption = row.get("interruption")
                        if (not isinstance(interruption, dict) or
                                interruption.get("intent_token") != self.released["intent_token"] or
                                interruption.get("record") != self.released["owner_release"]):
                            raise ValueError("terminal conflicts with physical release")
                    self.terminal = copy.deepcopy(row)
        except (ValueError, TypeError, AttributeError) as exc:
            if self.uncertainty is None: self.uncertainty = str(exc)
        return self.view()

    def view(self):
        state = ("needs_reconciliation" if self.uncertainty else
                 "terminal_received" if self.terminal else
                 "input_released_terminal_pending" if self.released else
                 "awaiting_outcome")
        return {"state": state, "action_id": self.action_id,
                "physical_release_verified": self.released is not None,
                "program_terminal_pending": self.released is not None and self.terminal is None,
                "current_input_authority": False,
                "accepted": copy.deepcopy(self.accepted),
                "released": copy.deepcopy(self.released),
                "terminal": copy.deepcopy(self.terminal),
                "uncertainty": self.uncertainty}
