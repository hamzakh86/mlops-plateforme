"""
tests/test_project_artifacts.py
───────────────────────────────
Validations légères des artefacts de déploiement, monitoring et démonstration.

Ces tests ne démarrent ni Docker, ni Kubernetes, ni Groq. Ils garantissent que
les fichiers livrés avec le projet restent lisibles et cohérents en CI.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_example_payloads_are_valid_json():
    example_files = sorted((ROOT_DIR / "examples").glob("*.json"))
    assert example_files, "Aucun payload de démonstration trouvé dans examples/."

    for path in example_files:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
        assert isinstance(payload, dict), f"{path.name} doit contenir un objet JSON."


def test_grafana_dashboard_is_valid_and_has_expected_panels():
    dashboard_path = ROOT_DIR / "monitoring" / "grafana" / "dashboards" / "mlops-platform.json"
    with dashboard_path.open(encoding="utf-8") as file:
        dashboard = json.load(file)

    assert dashboard["title"] == "MLOps Platform Monitoring"

    panel_titles = {panel["title"] for panel in dashboard["panels"]}
    expected_titles = {
        "HTTP Request Rate",
        "LLM Fallbacks",
        "LLM p95 Latency",
        "LLM Requests By Endpoint",
        "Average RAG Retrieved Documents",
    }
    assert expected_titles.issubset(panel_titles)


def test_monitoring_compose_references_prometheus_and_grafana():
    compose = load_yaml(ROOT_DIR / "docker-compose.monitoring.yml")
    services = compose["services"]

    assert {"mlops-api", "prometheus", "grafana"}.issubset(services)
    assert "8000:8000" in services["mlops-api"]["ports"]
    assert "9090:9090" in services["prometheus"]["ports"]
    assert any(p in services["grafana"]["ports"] for p in ["3001:3000", "3000:3000"])


def test_kubernetes_manifests_are_parseable_and_configured():
    configmap = load_yaml(ROOT_DIR / "k8s" / "configmap.yaml")
    deployment = load_yaml(ROOT_DIR / "k8s" / "deployment.yaml")
    ghcr_patch = load_yaml(ROOT_DIR / "k8s" / "deployment-ghcr.yaml")
    service = load_yaml(ROOT_DIR / "k8s" / "service.yaml")
    hpa = load_yaml(ROOT_DIR / "k8s" / "hpa.yaml")

    assert configmap["kind"] == "ConfigMap"
    assert "GROQ_MODEL" in configmap["data"]

    container = deployment["spec"]["template"]["spec"]["containers"][0]
    env_sources = container["envFrom"]
    assert {"configMapRef": {"name": "ml-inference-config"}} in env_sources
    assert any(source.get("secretRef", {}).get("name") == "groq-api-secret" for source in env_sources)

    assert service["metadata"]["annotations"]["prometheus.io/path"] == "/metrics"
    assert hpa["spec"]["scaleTargetRef"]["name"] == deployment["metadata"]["name"]

    ghcr_container = ghcr_patch["spec"]["template"]["spec"]["containers"][0]
    assert ghcr_patch["metadata"]["name"] == deployment["metadata"]["name"]
    assert ghcr_container["name"] == container["name"]
    assert ghcr_container["image"].startswith("ghcr.io/")
    assert ghcr_container["imagePullPolicy"] == "IfNotPresent"


def test_secret_templates_do_not_contain_real_api_keys():
    files_to_scan = [
        ROOT_DIR / "k8s" / "groq-api-key.template.yaml",
        ROOT_DIR / "k8s" / "configmap.yaml",
        ROOT_DIR / "k8s" / "deployment.yaml",
        ROOT_DIR / ".env.example",
    ]
    secret_pattern = re.compile(r"\b(gsk|AIza|sk)-[A-Za-z0-9_\-]{16,}\b")

    for path in files_to_scan:
        content = path.read_text(encoding="utf-8")
        assert not secret_pattern.search(content), f"Secret potentiel détecté dans {path}"


def test_ci_workflow_runs_tests_and_builds_docker_image():
    workflow = load_yaml(ROOT_DIR / ".github" / "workflows" / "ci.yml")
    steps = workflow["jobs"]["test-and-build"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)

    assert workflow["permissions"]["packages"] == "write"
    assert any(step.get("uses") == "actions/setup-node@v4" for step in steps)
    assert "npm ci --prefix frontend" in commands
    assert "npm run build --prefix frontend" in commands
    assert "pytest tests/ -v" in commands
    assert "python src/train.py" in commands
    assert "ml-inference-api:ci" in commands
    assert "ml-inference-api:${{ steps.docker_meta.outputs.sha_short }}" in commands
    assert "${{ steps.docker_meta.outputs.image_repo }}:${{ steps.docker_meta.outputs.sha_short }}" in commands
    assert "${{ steps.docker_meta.outputs.image_repo }}:latest" in commands
    assert "--build-arg APP_VERSION=${{ steps.docker_meta.outputs.sha_short }}" in commands
    assert "--build-arg VCS_REF=${{ github.sha }}" in commands
    assert "docker login $REGISTRY" in commands
    assert "docker push ${{ steps.docker_meta.outputs.image_repo }}:latest" in commands

    push_steps = [step for step in steps if step.get("name") in {"Login to GitHub Container Registry", "Push Docker image"}]
    assert push_steps
    assert all(step.get("if") == "github.event_name == 'push'" for step in push_steps)


def test_dockerfile_exposes_opencontainers_metadata_labels():
    dockerfile = (ROOT_DIR / "Dockerfile").read_text(encoding="utf-8")

    assert "ARG APP_VERSION=dev" in dockerfile
    assert "ARG VCS_REF=local" in dockerfile
    assert "ARG BUILD_DATE=unknown" in dockerfile
    assert 'LABEL org.opencontainers.image.version="${APP_VERSION}"' in dockerfile
    assert 'LABEL org.opencontainers.image.revision="${VCS_REF}"' in dockerfile
    assert "FROM node:22-slim AS frontend-builder" in dockerfile
    assert "RUN npm run build" in dockerfile
    assert "COPY --from=frontend-builder /frontend/dist ./frontend/dist" in dockerfile


def test_frontend_dashboard_assets_are_present():
    frontend_dir = ROOT_DIR / "frontend"
    index = (frontend_dir / "index.html").read_text(encoding="utf-8")
    package = json.loads((frontend_dir / "package.json").read_text(encoding="utf-8"))
    app_jsx = (frontend_dir / "src" / "App.jsx").read_text(encoding="utf-8")
    styles = (frontend_dir / "src" / "styles.css").read_text(encoding="utf-8")

    assert "/src/main.jsx" in index
    assert "react" in package["dependencies"]
    assert "vite" in package["dependencies"]
    assert "lucide-react" in package["dependencies"]
    assert any(title in app_jsx for title in ["Prevision CA ITGate", "Prediction Iris"])
    assert "Question RAG" in app_jsx
    assert "Activite recente" in app_jsx
    assert "Prometheus" in app_jsx
    assert "Grafana" in app_jsx
    assert 'request("/predict"' in app_jsx
    assert 'request("/ask"' in app_jsx
    assert 'request("/extract"' in app_jsx
    assert 'request("/classify"' in app_jsx
    assert "display: grid" in styles


def test_ghcr_patch_renderer_generates_real_image(tmp_path):
    output = tmp_path / "deployment-ghcr.local.yaml"
    command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "render_k8s_ghcr_patch.py"),
        "--registry",
        "ghcr.io/example/mlops-platform",
        "--tag",
        "abc1234",
        "--output",
        str(output),
    ]

    result = subprocess.run(command, cwd=ROOT_DIR, capture_output=True, text=True, check=True)
    rendered = load_yaml(output)
    image = rendered["spec"]["template"]["spec"]["containers"][0]["image"]

    assert "Image Kubernetes: ghcr.io/example/mlops-platform/ml-inference-api:abc1234" in result.stdout
    assert image == "ghcr.io/example/mlops-platform/ml-inference-api:abc1234"
    assert "<owner>" not in output.read_text(encoding="utf-8")


def test_ghcr_patch_renderer_rejects_placeholders(tmp_path):
    command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "render_k8s_ghcr_patch.py"),
        "--registry",
        "ghcr.io/<owner>/<repo>",
        "--tag",
        "abc1234",
        "--output",
        str(tmp_path / "patch.yaml"),
    ]

    result = subprocess.run(command, cwd=ROOT_DIR, capture_output=True, text=True)

    assert result.returncode != 0
    assert "placeholder" in result.stderr


def test_windows_k8s_ghcr_script_documents_make_alternative():
    script = (ROOT_DIR / "scripts" / "k8s_deploy_ghcr.ps1").read_text(encoding="utf-8")

    assert "render_k8s_ghcr_patch.py" in script
    assert "kubectl apply -f k8s/configmap.yaml" in script
    assert "kubectl patch deployment ml-inference-deployment" in script
    assert "-ImageRegistry ghcr.io/owner/repo -ImageTag abc1234" in script


def test_docker_smoke_script_builds_runs_checks_and_cleans_up():
    script = (ROOT_DIR / "scripts" / "docker_smoke_test.ps1").read_text(encoding="utf-8")
    makefile = (ROOT_DIR / "Makefile").read_text(encoding="utf-8")

    assert "docker build" in script
    assert "docker run -d" in script
    assert "Invoke-RestMethod -Uri $healthUrl" in script
    assert "docker rm -f $Name" in script
    assert "finally" in script
    assert "docker-smoke" in makefile


def test_windows_demo_checklist_covers_main_scenarios():
    checklist = (ROOT_DIR / "docs" / "windows-demo-checklist.md").read_text(encoding="utf-8")

    expected_sections = [
        "Préparation",
        "Entraînement et MLflow",
        "API FastAPI",
        "Docker",
        "Monitoring",
        "Kubernetes local",
        "Kubernetes avec image GHCR",
        "Fallback Groq",
        "Message de conclusion",
    ]

    for section in expected_sections:
        assert section in checklist

    assert "python scripts/smoke_api.py --skip-llm" in checklist
    assert ".\\scripts\\docker_smoke_test.ps1 -ImageTag smoke" in checklist
    assert ".\\scripts\\k8s_deploy_ghcr.ps1" in checklist
