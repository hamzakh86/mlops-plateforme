"""
scripts/smoke_api.py
────────────────────
Vérifie rapidement que les endpoints principaux de l'API répondent.

Usage:
    python scripts/smoke_api.py
    python scripts/smoke_api.py --base-url http://127.0.0.1:8000 --skip-llm
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_example(filename: str) -> dict[str, Any]:
    with open(ROOT_DIR / "examples" / filename, encoding="utf-8") as file:
        return json.load(file)


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed
    except urllib.error.URLError as exc:
        return 0, {"error": str(exc.reason)}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_check(base_url: str, method: str, path: str, payload: dict[str, Any] | None, validator) -> None:
    status, body = request_json(base_url, method, path, payload)
    validator(status, body)
    print(f"OK  {method:4} {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke tests HTTP pour l'API MLOps.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="URL racine de l'API.")
    parser.add_argument("--skip-llm", action="store_true", help="Ignore /ask, /extract et /classify.")
    args = parser.parse_args()

    checks = [
        (
            "GET",
            "/health",
            None,
            lambda status, body: (
                expect(status == 200, f"/health attendu 200, reçu {status}: {body}"),
                expect(body.get("status") == "ok", f"/health status inattendu: {body}"),
            ),
        ),
        (
            "POST",
            "/predict",
            load_example("predict_iris.json"),
            lambda status, body: (
                expect(status == 200, f"/predict attendu 200, reçu {status}: {body}"),
                expect(len(body.get("predictions", [])) == 2, f"/predict réponse invalide: {body}"),
            ),
        ),
    ]

    if not args.skip_llm:
        checks.extend(
            [
                (
                    "POST",
                    "/ask",
                    load_example("ask_monitoring.json"),
                    lambda status, body: (
                        expect(status == 200, f"/ask attendu 200, reçu {status}: {body}"),
                        expect("answer" in body and "sources" in body, f"/ask réponse invalide: {body}"),
                    ),
                ),
                (
                    "POST",
                    "/extract",
                    load_example("extract_invoice.json"),
                    lambda status, body: (
                        expect(status == 200, f"/extract attendu 200, reçu {status}: {body}"),
                        expect("extracted_data" in body, f"/extract réponse invalide: {body}"),
                    ),
                ),
                (
                    "POST",
                    "/classify",
                    load_example("classify_document.json"),
                    lambda status, body: (
                        expect(status == 200, f"/classify attendu 200, reçu {status}: {body}"),
                        expect("category" in body, f"/classify réponse invalide: {body}"),
                    ),
                ),
            ]
        )

    try:
        for method, path, payload, validator in checks:
            run_check(args.base_url, method, path, payload, validator)
    except AssertionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print("Smoke API terminé avec succès.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
