#!/usr/bin/env python3
"""Build a deterministic source archive without installing packaging dependencies."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import uuid
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
FILES = ["README.md", "LICENSE", "CONTRIBUTING.md", "ARCHITECTURE.md", "EXPERIMENTS.md",
         "SOURCES.md", "ROADMAP.md", "TASKS.md", "STATUS.md"]
DIRECTORIES = ["continuum", "examples", "tests", "tools", "docs", "plan"]
SUFFIXES = {".py", ".json", ".md", ".html", ".txt", ".csv"}


def sources() -> list[Path]:
    paths = {ROOT / name for name in FILES}
    for folder in DIRECTORIES:
        for path in (ROOT / folder).rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                raise ValueError(f"Release source must not be a symlink: {path.relative_to(ROOT)}")
            if path.is_file() and path.suffix in SUFFIXES:
                paths.add(path)
    for folder in [ROOT / "evidence" / "runtime"]:
        if folder.exists():
            for path in folder.rglob("*"):
                if path.is_symlink():
                    raise ValueError("Release evidence must not contain symlinks")
                if path.is_file() and path.suffix in SUFFIXES:
                    paths.add(path)
    retrievals = ROOT / "evidence" / "source-retrievals.json"
    if retrievals.is_file():
        paths.add(retrievals)
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or unsafe release input: {path.relative_to(ROOT)}")
    return sorted(paths)


def build(destination: Path) -> dict:
    inputs = sources()
    manifest = {"schema_version": 1, "package": "research-continuum", "version": VERSION,
                "license": "AGPL-3.0-only", "runtime": "Python standard library; Linux",
                "files": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                           "bytes": p.stat().st_size} for p in inputs]}
    # Materialize bytes once: the manifest and archive must describe the same snapshot.
    data = {str(p.relative_to(ROOT)): p.read_bytes() for p in inputs}
    for item in manifest["files"]:
        if hashlib.sha256(data[item["path"]]).hexdigest() != item["sha256"]:
            raise ValueError("Source changed while packaging; retry after writers finish")
    data["PACKAGE-MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.staging")
    try:
        with staging.open("xb") as raw:
            with gzip.GzipFile(fileobj=raw, filename="", mode="wb", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for name, content in sorted(data.items()):
                        info = tarfile.TarInfo(f"research-continuum-{VERSION}/{name}")
                        info.size = len(content)
                        info.mode = 0o644
                        info.mtime = 0
                        info.uid = info.gid = 0
                        info.uname = info.gname = ""
                        archive.addfile(info, io.BytesIO(content))
            raw.flush()
            os.fsync(raw.fileno())
        with tarfile.open(staging, "r:gz") as archive:
            if len(archive.getmembers()) != len(data):
                raise ValueError("Incomplete source archive")
        os.link(staging, destination)
        parent_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        staging.unlink(missing_ok=True)
    return {"filename": destination.name, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "bytes": destination.stat().st_size, "files": len(data), "version": VERSION}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New .tar.gz file; refuses existing files")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.out), indent=2))
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
