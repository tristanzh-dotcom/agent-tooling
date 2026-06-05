#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


MIN_GORDEN = (1, 0, 7)
MAX_GORDEN = (2, 0, 0)
DEFAULT_GORDEN_ROOT = Path("/Users/tristanzh/agent/.ai_skills/gorden-ppt-skill")


def parse_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "y"}


def parse_version(value: str) -> tuple[int, int, int]:
    parts = value.strip().split(".")
    nums = [int(part) for part in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def version_in_range(value: str) -> bool:
    parsed = parse_version(value)
    return MIN_GORDEN <= parsed < MAX_GORDEN


def render_dependencies_available() -> bool:
    return bool((shutil.which("soffice") or shutil.which("libreoffice")) and shutil.which("pdftoppm"))


def qa_payload(render_available: bool) -> dict[str, object]:
    if render_available:
        return {"qa_mode": "rendered_visual", "rendered_visual_verification": True}
    return {"qa_mode": "structural_only", "rendered_visual_verification": False}


def work_dir(timestamp: str, root: Path | None = None) -> Path:
    base = Path.cwd() if root is None else root
    return base / "work" / "ppt-maker" / timestamp


def qa_report(render_available: bool, unknown_images: list[dict[str, object]] | None = None) -> dict[str, object]:
    payload = qa_payload(render_available)
    payload["needs_visual_confirmation"] = list(unknown_images or [])
    return payload


def validate_mode_inputs(mode: str, source_pptx: Path | None = None) -> list[str]:
    if mode in {"template_preserving_edit", "template_replacement"} and source_pptx is None:
        return ["source_pptx_required"]
    return []


def validate_gorden(gorden_root: Path) -> tuple[dict[str, object], list[str]]:
    issues: list[str] = []
    version_path = gorden_root / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else ""
    if not version:
        issues.append("missing_gorden_version")
    compatible = bool(version and version_in_range(version))
    if version and not compatible:
        issues.append("unsupported_gorden_version")
    for relative in ("scripts/build_pptx.py", "scripts/render_slides.py", "templates/INDEX.md"):
        if not (gorden_root / relative).exists():
            issues.append(f"missing_gorden_asset:{relative}")
    return {"root": str(gorden_root), "version": version, "compatible": compatible}, issues


def validate_environment(
    *,
    mode: str,
    gorden_root: Path = DEFAULT_GORDEN_ROOT,
    source_pptx: Path | None = None,
    render_available: bool | None = None,
) -> dict[str, object]:
    gorden, issues = validate_gorden(gorden_root)
    issues.extend(validate_mode_inputs(mode, source_pptx))
    actual_render = render_dependencies_available() if render_available is None else render_available
    status = "ok" if not issues else "blocked"
    return {
        "schema": "ppt-maker-validation/v1",
        "status": status,
        "mode": mode,
        "gorden": gorden,
        "qa": qa_report(actual_render),
        "issues": issues,
    }


def run_cli(argv: list[str] | None = None) -> dict[str, object]:
    parser = argparse.ArgumentParser(description="Validate ppt-maker request dependencies.")
    parser.add_argument("--mode", choices=("prompt_to_ppt", "template_preserving_edit", "template_replacement"), required=True)
    parser.add_argument("--gorden-root", type=Path, default=DEFAULT_GORDEN_ROOT)
    parser.add_argument("--source-pptx", type=Path)
    parser.add_argument("--render-available", choices=("true", "false"))
    args = parser.parse_args(argv)
    render_available = None if args.render_available is None else parse_bool(args.render_available)
    payload = validate_environment(
        mode=args.mode,
        gorden_root=args.gorden_root,
        source_pptx=args.source_pptx,
        render_available=render_available,
    )
    if argv is None:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def main() -> int:
    payload = run_cli()
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
