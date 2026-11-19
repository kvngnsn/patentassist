#!/usr/bin/env python3
"""Offline source-release hygiene checks; not a comprehensive privacy/security audit."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"SKILL.md", "README.md", "LICENSE", ".gitignore", ".gitattributes", "requirements.txt"}
ROOT_DIRS = {".github", "phases", "modules", "references", "scripts", "templates", "tests", "evals"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yml", ".yaml", ".html"}
PATTERNS = {
    "private home path": r"/(?:Users|home)/[A-Za-z0-9._-]+/",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
    "provider token": r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}\b",
    "cloud access key": r"\bAKIA[A-Z0-9]{16}\b",
}


def check(root=ROOT):
    errors = []
    for path in root.iterdir():
        if path.name == ".git":
            continue
        if path.is_symlink():
            errors.append("Unexpected symlink: " + path.name)
        elif path.name not in (ROOT_DIRS if path.is_dir() else ROOT_FILES):
            errors.append("Unexpected root entry: " + path.name)
    for rel in ("SKILL.md", "README.md", "LICENSE", "references/resources.md",
                "references/examiner-review.md", "scripts/review.py", "tests/fixtures/README.md"):
        if not (root / rel).is_file():
            errors.append("Required release file missing: " + rel)
    for top in sorted(ROOT_DIRS | ROOT_FILES):
        base = root / top
        candidates = base.rglob("*") if base.is_dir() else [base]
        for path in candidates:
            if not path.exists():
                continue
            rel = str(path.relative_to(root))
            if path.is_symlink():
                errors.append("Unexpected symlink: " + rel)
                continue
            if path.name in ("__pycache__", ".DS_Store", ".env", "node_modules") or path.suffix in (".pyc", ".key", ".pem", ".log"):
                errors.append("Generated/private entry: " + rel)
            if not path.is_file():
                continue
            if path.suffix not in TEXT_SUFFIXES and path.name not in ROOT_FILES:
                if not (path.suffix == ".pdf" and path.parent == root / "tests/fixtures/colline"):
                    errors.append("Unreviewed binary/file type: " + rel)
                continue
            text = path.read_text(encoding="utf-8")
            for label, pattern in PATTERNS.items():
                if re.search(pattern, text):
                    errors.append(label + ": " + rel)  # Never echo matched secrets.
            if path.suffix == ".md":
                for link in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
                    link = unquote(link.strip("<>").split("#")[0])
                    if not link or re.match(r"[a-zA-Z]+:", link):
                        continue
                    if not (path.parent / link).exists():
                        errors.append("Broken local link in %s: %s" % (rel, link))
    return sorted(set(errors))


if __name__ == "__main__":
    findings = check()
    print("\n".join(findings) if findings else "Release structure, local links and common private/secret patterns: PASS")
    raise SystemExit(bool(findings))
