"""
scripts/render_k8s_ghcr_patch.py
─────────────────────────────────
Génère un patch Kubernetes local pour déployer l'image publiée dans GHCR.
"""

import argparse
import re
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT_DIR / "k8s" / "deployment-ghcr.yaml"
DEFAULT_OUTPUT = ROOT_DIR / "k8s" / "deployment-ghcr.local.yaml"
IMAGE_NAME = "ml-inference-api"


def validate_registry(registry: str) -> str:
    registry = registry.strip().rstrip("/")
    if not registry:
        raise ValueError("Le registry ne doit pas être vide.")
    if "<" in registry or ">" in registry:
        raise ValueError("Le registry contient encore un placeholder.")
    if not registry.startswith("ghcr.io/"):
        raise ValueError("Le registry doit commencer par ghcr.io/.")
    return registry.lower()


def validate_tag(tag: str) -> str:
    tag = tag.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", tag):
        raise ValueError("Le tag Docker contient des caractères invalides.")
    return tag


def render_patch(template_path: Path, output_path: Path, registry: str, tag: str) -> str:
    registry = validate_registry(registry)
    tag = validate_tag(tag)
    image = f"{registry}/{IMAGE_NAME}:{tag}"

    with template_path.open(encoding="utf-8") as file:
        manifest = yaml.safe_load(file)

    container = manifest["spec"]["template"]["spec"]["containers"][0]
    container["image"] = image
    container["imagePullPolicy"] = "IfNotPresent"

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        yaml.safe_dump(manifest, file, sort_keys=False, allow_unicode=True)

    return image


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère le patch Kubernetes GHCR local.")
    parser.add_argument("--registry", required=True, help="Registry complet, ex: ghcr.io/owner/repo")
    parser.add_argument("--tag", required=True, help="Tag Docker à déployer, ex: abc1234 ou v0.1.0")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    image = render_patch(args.template, args.output, args.registry, args.tag)
    print(f"Patch généré: {args.output}")
    print(f"Image Kubernetes: {image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
