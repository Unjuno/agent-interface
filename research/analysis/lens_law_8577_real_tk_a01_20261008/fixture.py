"""Disposable Tk widgets and a real Tcl/Tk event queue for Issue #8577."""

from __future__ import annotations

import tkinter as tk


class DisposableWidgetFixture:
    def __init__(self, case: dict):
        self.faults = set(case.get("faults", []))
        self.root = tk.Tk()
        self.root.title("Disposable Agent Interface lens-law fixture")
        self.root.geometry("260x120+0+0")
        self.epoch = 1
        self.values = {"primary": tk.StringVar(value="alpha"), "decoy": tk.StringVar(value="")}
        self.checked = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Ready")
        self.receipt = "complete"
        self.event_log: list[dict] = []
        self._request: dict | None = None
        self._delivery_count = 0
        self._first_value: str | None = None
        self._completion_after_id: str | None = None
        self._key_sequence = 0
        self._request_sequence = 0
        self.non_idempotent_count = 0

        self.entries: dict[str, tk.Entry] = {}
        for name in ("primary", "decoy"):
            entry = tk.Entry(self.root, name=name, textvariable=self.values[name])
            entry.pack()
            entry.bind("<KeyPress>", lambda event, field=name: self._on_keypress(event, field), add="+")
            self.entries[name] = entry

        self.status_label = tk.Label(self.root, name="status", textvariable=self.status)
        self.status_label.pack()
        self.check = tk.Checkbutton(self.root, name="checked", text="Enabled", variable=self.checked,
                                    command=self._on_checked)
        self.check.pack()
        self.counter_button = tk.Button(self.root, name="counter", text="Increment",
                                        command=self._increment_counter)
        self.counter_button.pack()

        if "duplicate_callback" in self.faults:
            field = "decoy" if "wrong_field" in self.faults else "primary"
            self.entries[field].bind("<KeyPress>", lambda event, key=field: self._on_keypress(event, key), add="+")
        self.pump()

    def pump(self) -> None:
        self.root.update()

    def focus(self, field: str) -> None:
        widget = self.check if field == "checked" else self.entries[field]
        widget.focus_force()
        self.pump()

    def focus_name(self) -> str | None:
        focused = self.root.focus_get()
        if focused is self.check:
            return "checked"
        return next((name for name, widget in self.entries.items() if focused is widget), None)

    def public_view(self, field: str) -> dict:
        if field in self.values:
            value = self.values[field].get()
        elif field == "checked":
            value = bool(self.checked.get())
        else:
            value = self.non_idempotent_count
        return {"field": field, "value": value, "status_label": self.status_label.cget("text"),
                "completion": self.receipt, "epoch": self.epoch, "focus": self.focus_name()}

    def issue_text(self, intended: str, value: str) -> dict:
        if self.values[intended].get() == value:
            self.event_log.append({"kind": "noop", "field": intended, "value": value})
            return {"dispatched": False, "target": intended}
        target = "decoy" if "wrong_field" in self.faults else intended
        if self.focus_name() != target:
            self.focus(target)
        self._request_sequence += 1
        self._request = {"field": intended, "value": value, "request_id": self._request_sequence}
        self.receipt = "pending" if "delayed" in self.faults else "complete"
        self.event_log.append({"kind": "text_request", "target": target, "intended": intended,
                               "value": value, "request_id": self._request_sequence, "epoch": self.epoch})
        if "delayed" in self.faults and self._completion_after_id is None:
            self._completion_after_id = self.root.after(250, self._complete)
            self.event_log.append({"kind": "completion_scheduled", "delay_ms": 250})

        entry = self.entries[target]
        entry.selection_range(0, "end")
        self._send_key(target, "BackSpace")
        for character in value:
            self._send_key(target, character)
        if "first_write_wins" in self.faults and self._first_value is None:
            self._first_value = self.values[target].get()
        return {"dispatched": True, "target": target}

    def _send_key(self, field: str, keysym: str) -> None:
        self._key_sequence += 1
        key_id = self._key_sequence
        self._delivery_count = 0
        self.event_log.append({"kind": "key_queued", "field": field, "keysym": keysym,
                               "key_id": key_id, "request_id": self._request["request_id"] if self._request else None})
        self.entries[field].event_generate("<KeyPress>", keysym=keysym, when="tail")
        self.entries[field].event_generate("<KeyRelease>", keysym=keysym, when="tail")
        self.pump()

    def _on_keypress(self, event: tk.Event, widget_field: str) -> str | None:
        if self._request is None:
            return "break"
        self._delivery_count += 1
        key = next((item for item in reversed(self.event_log) if item.get("kind") == "key_queued"), None)
        item = {"kind": "key_callback", "widget": widget_field, "intended": self._request["field"],
                "request_id": self._request["request_id"], "key_id": key["key_id"] if key else None,
                "keysym": event.keysym, "delivery": self._delivery_count, "epoch": self.epoch}
        self.event_log.append(item)
        if "ignored" in self.faults:
            self.status.set("Ignored input")
            item["effect"] = "ignored"
            return "break"
        if "first_write_wins" in self.faults and self._first_value is not None:
            self.status.set("First write retained")
            item["effect"] = "rejected_after_first"
            return "break"
        if self._delivery_count > 1:
            self.status.set("Duplicate callback")
            item["effect"] = "duplicate"
        else:
            self.status.set("Applied once")
            item["effect"] = "applied"
        return None

    def _complete(self) -> None:
        self.receipt = "complete"
        self._completion_after_id = None
        self.event_log.append({"kind": "completion_receipt", "epoch": self.epoch})

    def wait_for_completion(self) -> None:
        if self.receipt == "pending":
            self.root.after(400, self.root.quit)
            self.root.mainloop()
            self.pump()

    def issue_checked(self, expected: bool) -> None:
        self.focus("checked")
        if bool(self.checked.get()) == expected:
            self.event_log.append({"kind": "noop", "field": "checked", "value": expected})
            return
        self.event_log.append({"kind": "key_queued", "field": "checked", "keysym": "space"})
        self.check.event_generate("<KeyPress-space>", when="tail")
        self.check.event_generate("<KeyRelease-space>", when="tail")
        self.pump()

    def _on_checked(self) -> None:
        self.status.set("Applied once")
        self.event_log.append({"kind": "checkbutton_command", "value": bool(self.checked.get()), "epoch": self.epoch})

    def advance_epoch(self) -> None:
        self.epoch += 1
        self.event_log.append({"kind": "epoch_advanced", "epoch": self.epoch})

    def _increment_counter(self) -> None:
        self.non_idempotent_count += 1
        self.event_log.append({"kind": "non_idempotent_command", "count": self.non_idempotent_count})

    def raw_snapshot(self) -> dict:
        return {"widget_values": {key: variable.get() for key, variable in self.values.items()},
                "checked": bool(self.checked.get()), "status_label": self.status_label.cget("text"),
                "completion": self.receipt, "epoch": self.epoch, "focus": self.focus_name(),
                "non_idempotent_count": self.non_idempotent_count, "event_log": list(self.event_log)}

    def close(self) -> None:
        try:
            self.root.destroy()
        except tk.TclError:
            pass
