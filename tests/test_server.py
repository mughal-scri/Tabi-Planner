"""Local HTTP API tests using only ephemeral localhost ports."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from travelplanner.models import Profile
from travelplanner.planner import plan_to_dict, plan_trip
from travelplanner.server import create_server

DATA = "data/japan_travel_dataset.json"


def test_server_refuses_non_loopback_binding():
    with pytest.raises(ValueError, match="127.0.0.1"):
        create_server(DATA, host="0.0.0.0", port=0)


@pytest.fixture
def running_server():
    server = create_server(DATA, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        yield base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get_json(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return response.status, json.load(response)


def post_json(base, body):
    request = urllib.request.Request(
        base + "/api/plan", data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.load(response)


def test_static_routes_and_fixed_whitelist(running_server):
    for path, expected_type in (("/", "text/html"), ("/styles.css", "text/css"),
                                ("/app.js", "javascript")):
        with urllib.request.urlopen(running_server + path, timeout=5) as response:
            assert response.status == 200
            assert expected_type in response.headers["Content-Type"]
            assert response.read()
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(running_server + "/%2e%2e/DOCS/AGENT_BOARD.md", timeout=5)
    assert error.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(running_server + "/README.md", timeout=5)
    assert error.value.code == 404


def test_cities_and_category_pool_endpoints(running_server):
    status, cities = get_json(running_server, "/api/cities")
    assert status == 200
    assert len(cities) == 12
    assert cities[0]["id"] == "tokyo"
    assert {"name", "region", "places", "verified"} <= cities[0].keys()
    status, pool = get_json(running_server, "/api/categories?cities=tokyo")
    assert status == 200
    assert sum(item["count"] for item in pool) == 18
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(running_server + "/api/categories?cities=unknown", timeout=5)
    assert error.value.code == 400
    assert json.load(error.value)["error"]


def test_plan_endpoint_matches_python_plan(running_server):
    body = {
        "age_group": "adult",
        "route": [{"city_id": "tokyo", "days": 1}, {"city_id": "kyoto", "days": 1}],
        "interests": ["temple"],
        "algorithm": "astar",
    }
    status, result = post_json(running_server, body)
    expected = plan_to_dict(plan_trip(DATA, Profile("adult", (("tokyo", 1), ("kyoto", 1)),
                                       ("temple",))))
    assert status == 200
    assert result == expected


@pytest.mark.parametrize("body", [
    b"{", json.dumps({"age_group": "adult", "route": [{"city_id": "unknown", "days": 1}]}).encode(),
    json.dumps({"age_group": "adult", "route": [{"city_id": "tokyo", "days": 1}],
                "interests": ["unknown"]}).encode(),
    json.dumps({"age_group": "unknown", "route": [{"city_id": "tokyo", "days": 1}]}).encode(),
])
def test_bad_plan_requests_return_json_400(running_server, body):
    request = urllib.request.Request(
        running_server + "/api/plan", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request, timeout=5)
    assert error.value.code == 400
    assert json.load(error.value)["error"]


def test_oversized_body_returns_400_without_processing(running_server):
    request = urllib.request.Request(
        running_server + "/api/plan", data=b" " * (64 * 1024 + 1),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request, timeout=5)
    assert error.value.code == 400
    assert "64 KB" in json.load(error.value)["error"]
