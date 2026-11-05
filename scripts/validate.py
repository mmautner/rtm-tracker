"""Check data/commitments.yaml and data/milestones.yaml. Exit 1 on any error.

    .venv/bin/python scripts/validate.py

Runs in CI on every push and inside build_site.py, so a bad entry can't be published.
"""
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.schema import (  # noqa: E402
    AGENCIES, CATEGORIES, COMMITMENT_FIELDS, MILESTONE_RESPONSIBLE, OPTIONAL_FIELDS,
    PHASES, SOURCE_TYPES, STATUSES,
)

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_date(v):
    return isinstance(v, datetime.date) and not isinstance(v, datetime.datetime)


def host_ok(url, hosts):
    h = (urlparse(url).hostname or "").lower()
    return any(h == a or h.endswith("." + a) for a in hosts)


def check_sources(where, sources, hosts, errors):
    if not isinstance(sources, list) or not sources:
        errors.append(f"{where}: needs at least one source")
        return
    for i, s in enumerate(sources):
        w = f"{where}: sources[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{w}: must be a mapping with title, url, page, type")
            continue
        if not str(s.get("title") or "").strip():
            errors.append(f"{w}: missing title")
        url = str(s.get("url") or "").strip()
        if not url:
            errors.append(f"{w}: missing url")
        elif urlparse(url).scheme not in ("http", "https"):
            errors.append(f"{w}: url must start with http(s):// ({url})")
        elif not host_ok(url, hosts):
            errors.append(
                f"{w}: {urlparse(url).hostname} is not a primary-source host. If it is one "
                "(MTC, an agency, or the Legislature), add it to primary_source_hosts in site/config.json"
            )
        if "page" not in s:
            errors.append(f"{w}: missing page (use null if the source has no pages)")
        elif s["page"] is not None and not isinstance(s["page"], (int, str)):
            errors.append(f"{w}: page must be a number, text like \"5-6\", or null")
        if s.get("type") not in SOURCE_TYPES:
            errors.append(f"{w}: type must be one of {sorted(SOURCE_TYPES)}")


def validate(commitments, milestones, hosts, today=None):
    today = today or datetime.date.today()
    errors = []

    # ---- milestones
    if not isinstance(milestones, list):
        return ["data/milestones.yaml: must be a list of milestones"]
    mids = {}
    for i, m in enumerate(milestones):
        where = f"milestones.yaml[{i}]"
        if not isinstance(m, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        mid = m.get("id")
        where = f"milestone {mid or '#'+str(i)}"
        if not isinstance(mid, str) or not ID_RE.match(mid):
            errors.append(f"{where}: id must be lowercase-with-hyphens")
        elif mid in mids:
            errors.append(f"{where}: duplicate id")
        mids[mid] = m
        for k in ("title", "short_title", "responsible", "statute", "sources", "status_as_of"):
            if k not in m:
                errors.append(f"{where}: missing {k}")
        if m.get("responsible") not in MILESTONE_RESPONSIBLE:
            errors.append(f"{where}: responsible must be one of {MILESTONE_RESPONSIBLE}")
        for k in ("deadline", "completed_on", "status_as_of"):
            if m.get(k) is not None and not is_date(m.get(k)):
                errors.append(f"{where}: {k} must be a YYYY-MM-DD date or null")
        rule = m.get("deadline_rule")
        if rule is not None:
            if not isinstance(rule, dict) or not isinstance(rule.get("days"), int) or not rule.get("after"):
                errors.append(f"{where}: deadline_rule needs 'after' (milestone id) and 'days' (integer)")
            if m.get("deadline") is not None:
                errors.append(f"{where}: use deadline or deadline_rule, not both")
        check_sources(where, m.get("sources"), hosts, errors)
        for j, e in enumerate(m.get("estimates") or []):
            if not str(e.get("text") or "").strip():
                errors.append(f"{where}: estimates[{j}] missing text")
            check_sources(f"{where}: estimates[{j}]", [e.get("source")] if e.get("source") else [], hosts, errors)
    for mid, m in mids.items():
        rule = m.get("deadline_rule") if isinstance(m, dict) else None
        if isinstance(rule, dict) and rule.get("after") not in mids:
            errors.append(f"milestone {mid}: deadline_rule.after '{rule.get('after')}' is not a milestone id")

    # ---- commitments
    if not isinstance(commitments, list):
        return errors + ["data/commitments.yaml: must be a list of entries"]
    seen = set()
    for i, c in enumerate(commitments):
        if not isinstance(c, dict):
            errors.append(f"commitments.yaml[{i}]: must be a mapping")
            continue
        cid = c.get("id")
        where = f"entry {cid or '#'+str(i)}"
        for k in COMMITMENT_FIELDS:
            if k not in c and k not in OPTIONAL_FIELDS:
                errors.append(f"{where}: missing field '{k}' (use null if unknown)")
        for k in c:
            if k not in COMMITMENT_FIELDS:
                errors.append(f"{where}: unknown field '{k}'")
        if not isinstance(cid, str) or not ID_RE.match(cid):
            errors.append(f"{where}: id must be lowercase-with-hyphens")
        elif cid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(cid)
        if c.get("agency") not in AGENCIES:
            errors.append(f"{where}: agency must be one of {list(AGENCIES)}")
        if c.get("phase") not in PHASES:
            errors.append(f"{where}: phase must be 1, 2, or implementation_plan")
        if not str(c.get("recommendation") or "").strip():
            errors.append(f"{where}: recommendation is empty")
        if c.get("category") not in CATEGORIES:
            errors.append(f"{where}: category must be one of {CATEGORIES}")
        sv = c.get("estimated_savings_usd")
        if sv is not None and (isinstance(sv, bool) or not isinstance(sv, (int, float))):
            errors.append(f"{where}: estimated_savings_usd must be a number or null")
        if not str(c.get("savings_basis") or "").strip():
            errors.append(f"{where}: savings_basis is required, even when the figure is null")
        rb = c.get("required_by")
        if not (is_date(rb) or (isinstance(rb, str) and rb in mids)):
            errors.append(f"{where}: required_by must be a date or a milestone id from milestones.yaml")
        tc = c.get("target_completion")
        if tc is not None and not (is_date(tc) or (isinstance(tc, str) and MONTH_RE.match(tc))):
            errors.append(f"{where}: target_completion must be YYYY-MM, YYYY-MM-DD, or null")
        if tc is not None and not str(c.get("target_completion_basis") or "").strip():
            errors.append(f"{where}: target_completion needs target_completion_basis")
        ba = c.get("board_action")
        if ba is not None:
            if not isinstance(ba, dict) or not str(ba.get("description") or "").strip():
                errors.append(f"{where}: board_action must be null or have a description")
            elif ba.get("date") is not None and not is_date(ba.get("date")):
                errors.append(f"{where}: board_action.date must be YYYY-MM-DD or null")
        st = c.get("status", "MISSING")
        if st not in STATUSES:
            errors.append(f"{where}: status '{st}' is invalid; use one of "
                          f"{[s for s in STATUSES if s]} or null")
        if st in ("adopted", "in_progress", "implemented", "not_adopted", "superseded") and not ba:
            errors.append(f"{where}: status '{st}' needs a board_action")
        sao = c.get("status_as_of")
        if not is_date(sao):
            errors.append(f"{where}: status_as_of must be a YYYY-MM-DD date")
        elif sao > today:
            errors.append(f"{where}: status_as_of {sao} is in the future")
        check_sources(where, c.get("sources"), hosts, errors)
        srcs = c.get("sources") if isinstance(c.get("sources"), list) else []
        if st is not None and st in STATUSES and all(
            isinstance(s, dict) and s.get("type") == "report" for s in srcs
        ):
            errors.append(f"{where}: a status other than null needs a source besides the review report")
        if c.get("notes") is not None and not isinstance(c.get("notes"), str):
            errors.append(f"{where}: notes must be text")
    return errors


def main():
    cfg = json.loads((ROOT / "site" / "config.json").read_text())
    errors = validate(
        load(ROOT / "data" / "commitments.yaml"),
        load(ROOT / "data" / "milestones.yaml"),
        cfg["primary_source_hosts"],
    )
    if errors:
        print(f"{len(errors)} problem(s) in data/:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)
    print("data/ OK")


if __name__ == "__main__":
    main()
