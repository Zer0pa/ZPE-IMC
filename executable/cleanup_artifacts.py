#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministically remove local build/runtime artifacts.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--with-venv", action="store_true", help="Also remove .venv under root.")
    return parser.parse_args()


def _collect_targets(root: Path, with_venv: bool) -> list[Path]:
    targets: list[Path] = []
    venv_root = root / ".venv"

    def _skip_for_policy(path: Path) -> bool:
        if with_venv:
            return False
        return venv_root in path.parents or path == venv_root

    for pattern in ("**/__pycache__", "**/.pytest_cache"):
        targets.extend(
            p
            for p in root.glob(pattern)
            if p.is_dir() and not _skip_for_policy(p)
        )

    code_dir = root / "code"
    targets.extend(
        p
        for p in (
            code_dir / "build",
            code_dir / "dist",
            code_dir / ".pytest_cache",
        )
        if p.exists()
    )
    targets.extend(p for p in code_dir.glob("*.egg-info") if p.exists())

    if with_venv and venv_root.exists():
        targets.append(venv_root)

    # Keep deterministic order and avoid duplicates.
    return sorted(set(targets), key=lambda p: str(p))


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        shutil.rmtree(path)


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()

    targets = _collect_targets(root, with_venv=args.with_venv)
    if not targets:
        print("NO_ARTIFACTS_FOUND")
        return 0

    for target in targets:
        _remove_path(target)
        print(f"REMOVED {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
