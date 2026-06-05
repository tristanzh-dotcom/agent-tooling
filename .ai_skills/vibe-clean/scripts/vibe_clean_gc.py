#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


CONFIRMATION = "确认执行清除指令"
IMMUNE_DIRS = {".git", "_archive_legacy", ".ai_skills", ".venv", "venv"}
AUDIT_ROUND_RE = re.compile(r"^deepseek_audit_feedback_r(\d+)\.md$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--today", required=True)
    parser.add_argument("--mode", choices=["dry-run", "execute"], required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--confirm", default="")
    return parser.parse_args()


def is_skill_file(relative_path: Path) -> bool:
    return relative_path.name == "SKILL.md" or relative_path.name.endswith("_skill.md")


def is_node_modules_cache(relative_path: Path) -> bool:
    parts = relative_path.parts
    return any(
        part == "node_modules" and index + 1 < len(parts) and parts[index + 1] == ".cache"
        for index, part in enumerate(parts)
    )


def should_skip(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in IMMUNE_DIRS for part in parts):
        return True
    if "node_modules" in parts and not is_node_modules_cache(relative_path):
        return True
    if relative_path.name == "audit_artifact_cleanup_catalog.md":
        return True
    if relative_path.name == ".env" or relative_path.name.startswith(".env."):
        return True
    return is_skill_file(relative_path)


def is_delete_dir_target(path: Path, relative_path: Path) -> bool:
    name = path.name
    return name in {".pytest_cache", "__pycache__", ".vitest"} or is_node_modules_cache(relative_path)


def is_delete_target(path: Path) -> bool:
    name = path.name
    return (
        name.endswith(".bak")
        or name.startswith("temp_")
        or name.startswith("test_draft_")
        or name.startswith("debug_") and name.endswith(".log")
        or name.endswith(".tmp.log")
        or name.endswith(".pyc")
        or name == ".DS_Store"
        or name.endswith(".swp")
        or name.endswith(".swo")
        or name.endswith("~")
    )


def is_archive_target(path: Path, today: str) -> bool:
    name = path.name
    if name.startswith("HANDOVER_") and name.endswith(".md"):
        return today not in name
    return False


def scan(root: Path, today: str) -> dict[str, list[str]]:
    delete: list[str] = []
    archive: list[str] = []
    audit_rounds: list[tuple[int, str]] = []
    delete_dirs: set[Path] = set()

    for path in sorted(root.rglob("*"), key=lambda item: (len(item.relative_to(root).parts), item.as_posix())):
        relative_path = path.relative_to(root)
        if any(parent in delete_dirs for parent in relative_path.parents):
            continue
        if should_skip(relative_path):
            continue
        relative = relative_path.as_posix()
        if path.is_dir() and is_delete_dir_target(path, relative_path):
            delete.append(relative)
            delete_dirs.add(relative_path)
            continue
        if not path.is_file():
            continue

        audit_match = AUDIT_ROUND_RE.match(path.name)
        if audit_match:
            audit_rounds.append((int(audit_match.group(1)), relative))
        elif is_delete_target(path):
            delete.append(relative)
        elif is_archive_target(path, today):
            archive.append(relative)

    if len(audit_rounds) > 1:
        max_round = max(round_number for round_number, _relative in audit_rounds)
        delete.extend(relative for round_number, relative in audit_rounds if round_number < max_round)

    delete.sort()
    archive.sort()
    return {"delete": delete, "archive": archive}


def render_markdown(report: dict[str, list[str]]) -> str:
    def lines(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] or ["- 无"]

    output: list[str] = [
        "🔍 **Vibe Clean 预演扫描报告**",
        "",
        "**🗑️ 拟物理删除 (Delete)**:",
        *lines(report["delete"]),
        "",
        "**📦 拟移入归档 (Move to _archive_legacy/)**:",
        *lines(report["archive"]),
        "",
        f"*TZ，请确认以上清理靶点无误。回复“{CONFIRMATION}”后，我将执行物理清理。*",
    ]
    return "\n".join(output) + "\n"


def execute(root: Path, report: dict[str, list[str]]) -> None:
    archive_root = root / "_archive_legacy"
    archive_root.mkdir(exist_ok=True)

    for relative in report["archive"]:
        source = root / relative
        destination = archive_root / relative
        if not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    for relative in report["delete"]:
        target = root / relative
        if target.is_symlink():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report = scan(root, args.today)

    if args.mode == "dry-run":
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            sys.stdout.write(render_markdown(report))
        return 0

    if args.confirm != CONFIRMATION:
        sys.stderr.write(f"refusing to execute without exact confirmation: {CONFIRMATION}\n")
        return 1

    execute(root, report)
    print("Vibe Clean 物理清剿完毕，环境已重置。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
