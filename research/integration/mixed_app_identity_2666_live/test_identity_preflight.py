from research.integration.mixed_app_identity_2666_live.identity_preflight import visible_records


def test_identity_record_shape(monkeypatch):
    class Result:
        stdout = "7\n"

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())
    records = visible_records({"DISPLAY": ":141"})
    assert records == [{
        "window_id": 7,
        "pid": 7,
        "title": "7",
        "wm_class": "7",
        "display": ":141",
    }]
