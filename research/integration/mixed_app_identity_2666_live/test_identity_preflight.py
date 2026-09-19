from research.integration.mixed_app_identity_2666_live.identity_preflight import visible_records

def test_identity_record_shape(monkeypatch):
    class Result:
        stdout = "7\n"
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())
    assert visible_records({"DISPLAY": ":141"}) == []
