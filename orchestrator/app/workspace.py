from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.config import settings


class Workspace:
    """Manages the temporary workspace where agents write artifacts."""

    def __init__(self, workspace_id: str | None = None):
        self.id = workspace_id or uuid.uuid4().hex[:12]
        self.root = Path(settings.workspace_base) / self.id
        self._ensure_created()

    def _ensure_created(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def write_file(self, relative_path: str, content: str) -> str:
        """Write a file to the workspace. Returns the full path."""
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return str(path)

    def read_file(self, relative_path: str) -> str:
        """Read a file from the workspace."""
        path = self.root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return path.read_text()

    def list_files(self, relative_dir: str = "") -> list[str]:
        """List all files in the workspace (relative paths)."""
        base = self.root / relative_dir
        if not base.exists():
            return []
        files = []
        for path in sorted(base.rglob("*")):
            if path.is_file():
                files.append(str(path.relative_to(self.root)))
        return files

    def file_exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()

    def count_lines(self) -> int:
        """Count total lines across all workspace files."""
        total = 0
        for path in self.root.rglob("*"):
            if path.is_file():
                try:
                    total += len(path.read_text().splitlines())
                except (UnicodeDecodeError, PermissionError):
                    pass
        return total

    def cleanup(self) -> None:
        """Remove the workspace directory."""
        if self.root.exists():
            shutil.rmtree(self.root)
