#!/usr/bin/env python3
"""Valida rastreabilidade spec → testes conforme specs/manifest.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "specs" / "manifest.yaml"

    with manifest_path.open(encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    errors: list[str] = []
    for story in manifest.get("user_stories", []):
        story_id = story["id"]
        status = story.get("status", "specified")
        tests = story.get("tests", [])

        if status == "verified" and not tests:
            errors.append(f"{story_id}: status=verified mas sem testes listados")

        for test_path in tests:
            full = root / test_path
            if not full.exists():
                errors.append(f"{story_id}: teste não encontrado: {test_path}")

    if errors:
        for err in errors:
            print(f"ERRO: {err}", file=sys.stderr)
        return 1

    verified = sum(1 for s in manifest["user_stories"] if s.get("status") == "verified")
    implemented = sum(1 for s in manifest["user_stories"] if s.get("status") == "implemented")
    specified = sum(1 for s in manifest["user_stories"] if s.get("status") == "specified")

    print(f"Specs OK — verified: {verified}, implemented: {implemented}, specified: {specified}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
