"""Local JSON API and static-file server for the planner UI."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .knowledge import DatasetBundle, category_pool, load_dataset_bundle
from .models import Profile
from .planner import DEFAULT_DATA, plan_to_dict, plan_trip

HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 64 * 1024
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class PlannerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, dataset_path, dataset_bundle):
        self.dataset_path = str(dataset_path)
        self.dataset_bundle: DatasetBundle = dataset_bundle
        self.cities, self.category_labels = dataset_bundle
        super().__init__(address, _make_handler(self))


def _make_handler(server: PlannerHTTPServer):
    class PlannerRequestHandler(BaseHTTPRequestHandler):
        def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, payload: dict | list) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self._send_bytes(status, body, "application/json; charset=utf-8")

        def _send_error_json(self, status: int, message: str) -> None:
            self._send_json(status, {"error": message})

        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path in STATIC_FILES:
                filename, content_type = STATIC_FILES[parsed.path]
                try:
                    body = (WEB_ROOT / filename).read_bytes()
                except OSError:
                    self._send_error_json(404, "Page asset not found")
                    return
                self._send_bytes(200, body, content_type)
                return

            if parsed.path == "/api/cities":
                payload = [
                    {
                        "id": city.city_id,
                        "name": city.name,
                        "region": city.region,
                        "places": len(city.places),
                        "verified": city.verified,
                    }
                    for city in server.cities.values()
                ]
                self._send_json(200, payload)
                return

            if parsed.path == "/api/categories":
                query = parse_qs(parsed.query, keep_blank_values=True)
                if "cities" in query:
                    city_ids = [item.strip() for item in query["cities"][0].split(",") if item.strip()]
                else:
                    city_ids = list(server.cities)
                try:
                    payload = category_pool(server.cities, server.category_labels, city_ids)
                except ValueError as exc:
                    self._send_error_json(400, str(exc))
                    return
                self._send_json(200, payload)
                return

            self._send_error_json(404, "Not found")

        def do_POST(self):
            if urlsplit(self.path).path != "/api/plan":
                self._send_error_json(404, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_error_json(400, "Invalid Content-Length")
                return
            if content_length < 0:
                self._send_error_json(400, "Invalid Content-Length")
                return
            if content_length > MAX_BODY_BYTES:
                self._send_error_json(400, "Request body exceeds the 64 KB limit")
                return
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                self._send_error_json(400, "Content-Type must be application/json")
                return
            try:
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Request body must be a JSON object")
                route = payload.get("route")
                if not isinstance(route, list):
                    raise ValueError("route must be a list")
                route_pairs = []
                for item in route:
                    if not isinstance(item, dict) or "city_id" not in item or "days" not in item:
                        raise ValueError("Each route item must contain city_id and days")
                    route_pairs.append((item["city_id"], item["days"]))
                interests = payload.get("interests", [])
                if not isinstance(interests, list):
                    raise ValueError("interests must be a list of category ids")
                age_group = payload.get("age_group")
                algorithm = payload.get("algorithm", "astar")
                if not isinstance(age_group, str):
                    raise ValueError("age_group must be a string")
                if any(not isinstance(interest, str) for interest in interests):
                    raise ValueError("interests must contain category id strings")
                if not isinstance(algorithm, str):
                    raise ValueError("algorithm must be a string")
                plan = plan_trip(
                    server.dataset_path,
                    Profile(age_group, tuple(route_pairs), tuple(interests)),
                    algorithm=algorithm,
                    dataset_bundle=server.dataset_bundle,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                self._send_error_json(400, str(exc))
                return
            self._send_json(200, plan_to_dict(plan))

    return PlannerRequestHandler


def create_server(
    dataset_path: str | Path = DEFAULT_DATA,
    host: str = HOST,
    port: int = PORT,
) -> PlannerHTTPServer:
    """Load data once and create a server bound to loopback only."""
    if host != HOST:
        raise ValueError(f"Server host must be {HOST}")
    dataset_bundle = load_dataset_bundle(dataset_path)
    return PlannerHTTPServer((host, port), dataset_path, dataset_bundle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Japan travel planner UI")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    args = parser.parse_args(argv)
    server = create_server(args.data, port=args.port)
    print(f"Japan Travel Planner: http://{HOST}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
