"""Offline network probe for the six-task append-only fixture."""

import json
import tempfile
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from integrated_efficiency_fixture_v1 import Fixture


def post(url: str, token: str) -> None:
    request = urllib.request.Request(
        url.replace("/task/", "/submit/"),
        data=urllib.parse.urlencode({"value": token}).encode(),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        assert response.status == 200


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="integrated-fixture-probe-") as temp:
        with Fixture(Path(temp), 991026) as fixture:
            goals = fixture.goals()
            assert [row["layout"] for row in goals] == ["A", "A", "A", "B", "B", "B"]
            assert len({row["token"] for row in goals}) == 6
            for goal in goals:
                with urllib.request.urlopen(goal["url"], timeout=2) as response:
                    page = response.read().decode()
                    assert goal["task_id"] in page
                post(goal["url"], goal["token"])
            result = fixture.evaluate()
            assert result["success"] is True
            assert result["record_count"] == 6
            assert all(count == 1 for count in result["exact_counts"].values())
            history = fixture.records()
            assert [row["task_id"] for row in history] == [row["task_id"] for row in goals]
            post(goals[0]["url"], goals[0]["token"])
            try:
                post(goals[1]["url"], "wrong-token")
                raise AssertionError("wrong token unexpectedly returned success")
            except urllib.error.HTTPError as exc:
                assert exc.code == 422
            negative = fixture.evaluate()
            assert negative["success"] is False
            assert negative["duplicates"] == {"task-1": 2}
            assert len(negative["unexpected"]) == 1
            print(json.dumps({"passed": True, "positive": result,
                              "duplicate_and_wrong_control": negative},
                             indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
