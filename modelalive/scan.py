from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from modelalive.check import alive

# Common LLM model ID patterns in source code and config
_MODEL_PATTERNS = [
    re.compile(r"""['"](claude-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](gpt-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](gemini-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](o[0-9]-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](text-embedding-[a-zA-Z0-9._-]{3,64})['"]"""),
    re.compile(r"""['"](ft:[^'"]{3,200})['"]"""),
    re.compile(r"""['"](llama-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](grok-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](deepseek-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](mistral-[a-zA-Z0-9._-]{3,128})['"]"""),
    re.compile(r"""['"](qwen[a-zA-Z0-9._-]{0,128})['"]"""),
    re.compile(r"""['"](anthropic\.claude-[a-zA-Z0-9._:-]{3,128})['"]"""),
    re.compile(r"""['"](amazon\.[a-zA-Z0-9._:-]{3,128})['"]"""),
    re.compile(
        r"""['"]((?:anthropic|openai|google|meta-llama|qwen|deepseek|mistral|x-ai)/[a-zA-Z0-9._:-]{3,128})['"]"""
    ),
    re.compile(r"""['"](meta-llama/[a-zA-Z0-9._:-]{3,128})['"]"""),
    re.compile(r"""model\s*[=:]\s*['"]([a-zA-Z0-9][a-zA-Z0-9._:/-]{2,127})['"]"""),
]

_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
}

_SKIP_FILES = {".min.js", ".map"}


@dataclass
class ScanFinding:
    path: str
    line: int
    model: str
    status: str
    replacement: str | None = None
    alive: bool = True


@dataclass
class ScanReport:
    root: str
    scanned_files: int = 0
    findings: list[ScanFinding] = field(default_factory=list)

    @property
    def retired(self) -> list[ScanFinding]:
        return [f for f in self.findings if f.status == "retired"]

    @property
    def deprecated(self) -> list[ScanFinding]:
        return [f for f in self.findings if f.status == "deprecated"]

    @property
    def unknown(self) -> list[ScanFinding]:
        return [f for f in self.findings if f.status == "unknown"]


def _should_scan(path: Path) -> bool:
    if any(part in _SKIP_DIRS for part in path.parts):
        return False
    if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf"}:
        return False
    if any(path.name.endswith(s) for s in _SKIP_FILES):
        return False
    return path.is_file()


def scan_path(
    root: str | Path,
    *,
    extensions: set[str] | None = None,
) -> ScanReport:
    root_path = Path(root).resolve()
    ext = extensions or {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".env",
        ".md",
        ".sh",
    }
    report = ScanReport(root=str(root_path))
    seen: set[tuple[str, int, str]] = set()

    for path in root_path.rglob("*"):
        if not _should_scan(path):
            continue
        if path.suffix not in ext and path.name not in {"Dockerfile", ".env"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        report.scanned_files += 1
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in _MODEL_PATTERNS:
                for match in pattern.finditer(line):
                    model = match.group(1)
                    key = (str(path.relative_to(root_path)), line_no, model)
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        result = alive(model)
                    except ValueError:
                        continue
                    if result.status == "active":
                        continue
                    report.findings.append(
                        ScanFinding(
                            path=key[0],
                            line=line_no,
                            model=model,
                            status=result.status,
                            replacement=result.replacement,
                            alive=result.alive,
                        )
                    )
    return report
