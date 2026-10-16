import json
import time
import tkinter as tk

CASES = [
    ("fast", 0.05, 0.20),
    ("delayed", 0.35, 0.20),
    ("absent", None, 0.20),
    ("late", 0.35, 0.50),
]

rows = []
for name, effect_delay, horizon in CASES:
    # Isolate each case so delayed callbacks cannot leak across cases.
    root = tk.Tk()
    root.geometry("320x120")
    root.withdraw()
    label = tk.Label(root, text="pending", width=30, height=4)
    label.pack()
    root.deiconify()
    root.update()
    start = time.monotonic()
    if effect_delay is not None:
        root.after(round(effect_delay * 1000), lambda: label.config(text="done"))
    state = "UNKNOWN"
    observed_at = None
    while time.monotonic() - start < horizon:
        root.update()
        if label.cget("text") == "done":
            state = "COMPLETED"
            observed_at = time.monotonic() - start
            break
        time.sleep(0.005)
    rows.append({
        "case": name,
        "effect_delay": effect_delay,
        "horizon": horizon,
        "state": state,
        "observed_at": observed_at,
        "proceeded": state == "COMPLETED",
    })
    root.destroy()

result = {
    "rows": rows,
    "unknown_count": sum(r["state"] == "UNKNOWN" for r in rows),
    "unsafe_timeout_as_completion": sum(r["state"] == "UNKNOWN" for r in rows),
    "scope": "Xvfb/Tk fixture; not production GUI evidence",
}
print(json.dumps(result, indent=2))
