"""
scripts/generate_demo_traffic.py
────────────────────────────────
Génère du trafic de démonstration vers l'API pour alimenter Prometheus/Grafana.

Usage:
    python scripts/generate_demo_traffic.py
    python scripts/generate_demo_traffic.py --base-url http://127.0.0.1:8000 --rounds 5
    python scripts/generate_demo_traffic.py --skip-llm
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any


import urllib.parse

PREDICT_PAYLOAD = {
    "data": [
        {
            "num_engineers": 45,
            "active_projects": 16,
            "avg_contract_value": 4800.0,
            "lag_1": 72500.0,
            "lag_2": 68000.0,
            "lag_3": 65400.0,
        }
    ]
}

DRIFT_PAYLOAD = {
    "data": [
        {
            "num_engineers": 450,
            "active_projects": 80,
            "avg_contract_value": 15000.0,
            "lag_1": 420000.0,
            "lag_2": 390000.0,
            "lag_3": 350000.0,
        }
    ]
}

ASK_PAYLOADS = [
    {"question": "Quels sont les horaires de travail chez ITGate Group ?"},
    {"question": "Comment la plateforme MLOps est-elle déployée ?"},
    {"question": "Que se passe-t-il si Groq est indisponible ?"},
]

EXTRACT_PAYLOADS = [
    {"text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND."},
    {"text": "Facture Cloud Services du 12/08/2026. Montant total: 320.00 TND."},
]

CLASSIFY_PAYLOADS = [
    {
        "text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.",
        "categories": ["Facture", "CV", "Contrat", "Rapport"],
    },
    {
        "text": "Rapport technique décrivant la supervision Prometheus et Grafana.",
        "categories": ["Facture", "CV", "Contrat", "Rapport"],
    },
]


def get_auth_token(base_url: str) -> str:
    url = f"{base_url.rstrip('/')}/token"
    data = urllib.parse.urlencode({"username": "admin", "password": "admin"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("access_token", "")
    except Exception as e:
        print(f"⚠️ Impossible d'obtenir le token JWT: {e}")
        return ""


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None, token: str = "") -> tuple[int, str]:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, body[:180]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body[:180]
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)


def run_round(base_url: str, round_index: int, skip_llm: bool, token: str) -> None:
    # Alterner entre requête normale et requête avec dérive
    predict_payload = DRIFT_PAYLOAD if (round_index % 2 == 1) else PREDICT_PAYLOAD
    calls: list[tuple[str, str, dict[str, Any] | None]] = [
        ("GET", "/health", None),
        ("POST", "/predict", predict_payload),
    ]

    if not skip_llm:
        calls.extend(
            [
                ("POST", "/ask", ASK_PAYLOADS[round_index % len(ASK_PAYLOADS)]),
                ("POST", "/extract", EXTRACT_PAYLOADS[round_index % len(EXTRACT_PAYLOADS)]),
                ("POST", "/classify", CLASSIFY_PAYLOADS[round_index % len(CLASSIFY_PAYLOADS)]),
            ]
        )

    for method, path, payload in calls:
        status, preview = request_json(base_url, method, path, payload, token=token)
        print(f"{method:4} {path:10} -> {status:3} | {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère du trafic de démonstration pour Prometheus/Grafana.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="URL racine de l'API FastAPI.")
    parser.add_argument("--rounds", type=int, default=5, help="Nombre de tours de requêtes à envoyer.")
    parser.add_argument("--delay", type=float, default=0.8, help="Pause en secondes entre deux tours.")
    parser.add_argument("--skip-llm", action="store_true", help="N'appelle que /health et /predict.")
    args = parser.parse_args()

    print(f"🔑 Récupération du token JWT sur {args.base_url}...")
    token = get_auth_token(args.base_url)
    if token:
        print("✅ Authentification réussie !")
    else:
        print("⚠️ Exécution sans token (les endpoints protégés renverront 401)")

    for index in range(args.rounds):
        print(f"\n--- Round {index + 1}/{args.rounds} ---")
        run_round(args.base_url, index, args.skip_llm, token)
        if index < args.rounds - 1:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
