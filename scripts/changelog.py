"""Build a field-level changelog from the git history of data/*.yaml.

Each commit that touched a data file becomes one changelog item listing what changed,
entry by entry: added, removed, or which fields changed (with old and new values).
Status changes are flagged so they can be shown first.

    .venv/bin/python scripts/changelog.py        # print as JSON
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FILES = ["data/commitments.yaml", "data/milestones.yaml"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def load_at(sha, path):
    """Parse a data file as it was at a commit; [] if it didn't exist or didn't parse."""
    try:
        text = git("show", f"{sha}:{path}")
    except subprocess.CalledProcessError:
        return []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return []
    return data if isinstance(data, list) else []


def by_id(items):
    return {i["id"]: i for i in items if isinstance(i, dict) and "id" in i}


def show(v):
    if v is None:
        return "null"
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str, ensure_ascii=False)
    return str(v)


def diff(old, new):
    o, n = by_id(old), by_id(new)
    out = []
    for i in n:
        if i not in o:
            out.append({"id": i, "kind": "added", "fields": [], "status_change": None,
                        "status": n[i].get("status")})
    for i in o:
        if i not in n:
            out.append({"id": i, "kind": "removed", "fields": [], "status_change": None})
    for i in n:
        if i in o and o[i] != n[i]:
            fields = []
            for k in sorted(set(o[i]) | set(n[i])):
                if o[i].get(k) != n[i].get(k):
                    fields.append({"field": k, "old": show(o[i].get(k)), "new": show(n[i].get(k))})
            sc = None
            if o[i].get("status") != n[i].get("status"):
                sc = {"old": o[i].get("status"), "new": n[i].get("status")}
            out.append({"id": i, "kind": "changed", "fields": fields, "status_change": sc})
    return out


def history():
    """List of commits (newest first) with their per-entry changes. [] outside a git repo."""
    try:
        git("rev-parse", "--git-dir")
        log = git("log", "--format=%H%x1f%P%x1f%ad%x1f%s", "--date=short", "--", *FILES)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    commits = []
    for line in log.splitlines():
        sha, parents, date, subject = line.split("\x1f", 3)
        parent = parents.split()[0] if parents else None
        changes = []
        for path in FILES:
            new = load_at(sha, path)
            old = load_at(parent, path) if parent else []
            for c in diff(old, new):
                c["file"] = path
                changes.append(c)
        if changes:
            commits.append({"sha": sha, "date": date, "subject": subject, "changes": changes})
    return commits


if __name__ == "__main__":
    json.dump(history(), sys.stdout, indent=2, default=str)
    print()
