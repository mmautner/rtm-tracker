"""Build the static site into dist/<base>/ from data/*.yaml.

    .venv/bin/python build_site.py          # production build
    .venv/bin/python build_site.py --dev    # also copy maxmautner.com's stylesheet and fonts into dist/
                                            # so a local preview looks like production

Pages: home (scorecard + timeline), one page per agency, methodology, changelog.
Exports: data/commitments.csv, data/commitments.json, data/milestones.json.
The build validates the data first and stops if anything is wrong.
"""
import argparse
import csv
import hashlib
import datetime
import io
import json
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from scripts import changelog  # noqa: E402
from scripts import og  # noqa: E402
from scripts.schema import (  # noqa: E402
    ACTION_TYPE_SOURCES, ACTION_TYPES, AGENCIES, CATEGORIES, FINDING_BASES, IOC_SEATS, PHASES, SOURCE_TYPES, STATUSES,
)
from scripts.validate import validate, validate_oversight  # noqa: E402

SITE = ROOT / "site"
CFG = json.loads((SITE / "config.json").read_text())
BASE = CFG["base"]
DIST = ROOT / "dist"
OUT = DIST / BASE.strip("/")
BLOG = ROOT.parent / "maxmautner"


def static_version():
    """Hash of site/static, appended to asset URLs (?v=) so browsers and CloudFront fetch new copies."""
    h = hashlib.sha256()
    for p in sorted(f for f in (SITE / "static").rglob("*") if f.is_file()):
        h.update(p.relative_to(SITE).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:10]

# Order of segments in the per-agency status bars: furthest along first.
BAR_ORDER = ["implemented", "in_progress", "adopted", "not_started", "missed", "not_adopted",
             "superseded", None]

# Out-of-scope recipients, from Gov. Code §67700 and §67750(b)(6)-(9), (13)-(16).
OUT_OF_SCOPE = [
    ("Livermore Amador Valley Transit Authority (Wheels)", "Alameda County small bus operator, §67750(b)(6)"),
    ("Union City Transit", "Alameda County small bus operator, §67750(b)(6)"),
    ("Central Contra Costa Transit Authority (County Connection)", "Contra Costa County small bus operator, §67750(b)(7)"),
    ("Western Contra Costa Transit Authority (WestCAT)", "Contra Costa County small bus operator, §67750(b)(7)"),
    ("Eastern Contra Costa Transit Authority (Tri Delta Transit)", "Contra Costa County small bus operator, §67750(b)(7)"),
    ("San Francisco Bay Ferry (WETA)", "§67750(b)(8)"),
    ("Golden Gate Transit (Golden Gate Bridge, Highway and Transportation District)", "§67750(b)(9)"),
    ("Alameda County Transportation Commission", "county share for public transit expenses and road repaving, §67750(b)(13)"),
    ("Contra Costa Transportation Authority", "county share for public transit expenses and road repaving, §67750(b)(14)"),
    ("San Mateo County Transit District (SamTrans)", "county share for public transit expenses and road repaving, §67750(b)(15)"),
    ("Santa Clara Valley Transportation Authority (VTA)", "county share for public transit expenses and road repaving, §67750(b)(16)"),
]


def load(name):
    with open(ROOT / "data" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fmt_date(d):
    if d is None:
        return ""
    if isinstance(d, str):  # YYYY-MM
        y, m = d.split("-")[:2]
        return datetime.date(int(y), int(m), 1).strftime("%B %Y")
    return f"{d:%B} {d.day}, {d.year}"


def fmt_usd(v):
    if v is None:
        return "Not estimated"
    return f"${v:,.0f}"


def status_key(s):
    return "unverified" if s is None else s


def resolve_milestones(milestones):
    """Compute deadlines from deadline_rule where the anchor milestone has a completion date."""
    by_id = {m["id"]: m for m in milestones}
    for m in milestones:
        m["computed_deadline"] = m.get("deadline")
        m["deadline_text"] = fmt_date(m.get("deadline")) if m.get("deadline") else ""
        rule = m.get("deadline_rule")
        if rule:
            anchor = by_id[rule["after"]]
            if anchor.get("completed_on"):
                m["computed_deadline"] = anchor["completed_on"] + datetime.timedelta(days=rule["days"])
                m["deadline_text"] = (f"{fmt_date(m['computed_deadline'])} "
                                      f"({rule['days']} days after “{anchor['short_title']}”)")
            else:
                m["deadline_text"] = (f"{rule['days']} days after “{anchor['short_title']}” "
                                      "(date not yet set)")
        elif not m.get("deadline"):
            m["deadline_text"] = "No statutory deadline"
    return by_id


def next_operator_deadline(milestones):
    for m in milestones:
        if m["responsible"] == "operators" and not m.get("completed_on"):
            return m
    return None


def to_csv(commitments, ms_by_id):
    buf = io.StringIO()
    cols = ["id", "agency", "phase", "recommendation", "category", "action_type", "action_type_basis", "action_type_source", "adopted_wording", "estimated_savings_usd",
            "savings_basis", "required_by", "required_by_date", "target_completion",
            "target_completion_basis", "board_action_date", "board_action_description", "status",
            "status_as_of", "source_count", "sources", "notes"]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for c in commitments:
        rb = c["required_by"]
        rb_date = ms_by_id[rb]["computed_deadline"] if rb in ms_by_id else rb
        ba = c.get("board_action") or {}
        w.writerow({
            "id": c["id"], "agency": c["agency"], "phase": c["phase"],
            "recommendation": c["recommendation"], "category": c["category"],
            "action_type": c["action_type"], "action_type_basis": c["action_type_basis"],
            "action_type_source": c["action_type_source"], "adopted_wording": c.get("adopted_wording") or "",
            "estimated_savings_usd": "" if c["estimated_savings_usd"] is None else c["estimated_savings_usd"],
            "savings_basis": c["savings_basis"], "required_by": rb,
            "required_by_date": rb_date or "",
            "target_completion": c.get("target_completion") or "",
            "target_completion_basis": c.get("target_completion_basis") or "",
            "board_action_date": ba.get("date") or "", "board_action_description": ba.get("description") or "",
            "status": c["status"] or "", "status_as_of": c["status_as_of"],
            "source_count": len(c["sources"]),
            "sources": " | ".join(
                f"{s['title']}" + (f" (p. {s['page']})" if s.get("page") is not None else "") + f" <{s['url']}>"
                for s in c["sources"]),
            "notes": c.get("notes") or "",
        })
    return buf.getvalue()


def moe_applies(basis):
    """Gov. Code §67770 (maintenance of effort) covers operators funded under §67750(b)(2)-(9)."""
    m = re.search(r"§67750\(b\)\((\d+)\)", basis)
    return bool(m) and 2 <= int(m.group(1)) <= 9


def atom_feed(history, entry_agency, status_label, updated):
    """Atom feed of the changelog: one entry per commit that touched data/."""
    site = CFG["site_url"] + BASE
    def iso(d):
        return f"{d}T00:00:00Z"
    entries = []
    for c in history:
        lines = []
        for ch in c["changes"]:
            if ch.get("status_change"):
                sc = ch["status_change"]
                lines.append(f"{ch['id']}: {status_label(sc['old'])} → {status_label(sc['new'])}")
        kinds = {}
        for ch in c["changes"]:
            kinds[ch["kind"]] = kinds.get(ch["kind"], 0) + 1
        summary = ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) or "no entry changes"
        html = "<p>" + xml_escape(summary) + "</p>"
        if lines:
            html += "<p>Status changes:</p><ul>" + "".join(f"<li>{xml_escape(x)}</li>" for x in lines) + "</ul>"
        html += f'<p><a href="{site}changelog/#c-{c["sha"][:7]}">See the full change</a></p>'
        entries.append(f"""  <entry>
    <title>{xml_escape(c["subject"])}</title>
    <id>{site}changelog/#c-{c["sha"][:7]}</id>
    <link href="{site}changelog/#c-{c["sha"][:7]}"/>
    <updated>{iso(c["date"])}</updated>
    <content type="html">{xml_escape(html)}</content>
  </entry>""")
    feed_updated = iso(history[0]["date"]) if history else iso(updated)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{xml_escape(CFG["site_title"])}: changes</title>
  <subtitle>Every change to the tracker's data: status changes, new entries, and corrections.</subtitle>
  <id>{site}changelog/</id>
  <link rel="self" href="{site}changelog.xml"/>
  <link href="{site}changelog/"/>
  <updated>{feed_updated}</updated>
  <author><name>{xml_escape(CFG["maintainer"])}</name></author>
{chr(10).join(entries)}
</feed>
"""


def write_dev_assets():
    """Copy the blog's stylesheet and fonts into dist/ so a local preview matches production."""
    page = BLOG / "_site" / "index.html"
    if not page.exists():
        print(f"--dev: no built blog at {page}; the preview will use fallback styles", file=sys.stderr)
        return
    css = re.search(r"<style>(.*?)</style>", page.read_text(), re.S).group(1)
    dest = DIST / CFG["site_css"].lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(css, encoding="utf-8")
    fonts = BLOG / "_site" / CFG["blog_fonts"].strip("/")
    if fonts.exists():
        shutil.copytree(fonts, DIST / CFG["blog_fonts"].strip("/"), dirs_exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true", help="also write local copies of the blog's CSS and fonts")
    args = ap.parse_args()
    commitments = load("commitments.yaml")
    milestones = load("milestones.yaml")
    oversight = load("oversight.yaml") or []
    errors = validate(commitments, milestones, CFG["primary_source_hosts"])
    errors += validate_oversight(oversight, CFG["primary_source_hosts"])
    if errors:
        print("Build stopped; fix data/ first:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    ms_by_id = resolve_milestones(milestones)
    nxt = next_operator_deadline(milestones)
    history = changelog.history()

    for c in commitments:
        c["skey"] = status_key(c["status"])
        c["required_by_milestone"] = ms_by_id.get(c["required_by"]) if isinstance(c["required_by"], str) else None
        c["phase_label"] = PHASES[c["phase"]]
        c["phase_key"] = str(c["phase"])

    agencies = []
    for name, (slug, display) in AGENCIES.items():
        rows = [c for c in commitments if c["agency"] == name]
        counts = {status_key(s): sum(1 for c in rows if c["status"] == s) for s in STATUSES}
        actions = {}
        for c in rows:
            ba = c.get("board_action")
            if ba and c["status"] != "not_adopted":
                actions.setdefault((ba.get("date"), ba["description"]), 0)
                actions[(ba.get("date"), ba["description"])] += 1
        bar = [{"key": status_key(st), "n": counts[status_key(st)],
                "pct": round(100 * counts[status_key(st)] / len(rows), 2) if rows else 0}
               for st in BAR_ORDER if counts[status_key(st)]]
        agencies.append({
            "name": name, "slug": slug, "display": display, "rows": rows, "bar": bar,
            "color": CFG["agency_colors"].get(name, "currentColor"),
            "ridership": CFG["agency_ridership"].get(name),
            "kinds": {k: sum(1 for c in rows if c["action_type"] == k) for k in ACTION_TYPES},
            "n_revenue": sum(1 for c in rows if c["category"] == "revenue"),
            "logo": CFG["agency_logos"].get(name, {}).get("file"),
            "logo_tile": CFG["agency_logos"].get(name, {}).get("tile", "#ffffff"),
            "counts": counts, "total": len(rows),
            "last_verified": max((c["status_as_of"] for c in rows), default=None),
            "actions": sorted(actions, key=lambda a: (a[0] is None, a[0] or datetime.date.min)),
        })

    statuses = [{"key": status_key(k), "value": k, **v} for k, v in STATUSES.items()]
    last_verified = max(c["status_as_of"] for c in commitments)
    totals = {status_key(st): sum(1 for c in commitments if c["status"] == st) for st in STATUSES}
    # MTC's estimated completion date for adopted strategies (Res. 4743). Shown only when every adopted
    # entry has the same one, so the summary never hides a difference.
    targets = {c.get("target_completion") for c in commitments if c["status"] in ("adopted", "in_progress")}
    target = None
    if len(targets) == 1 and None not in targets:
        target = {"month": next(iter(targets)), "text": fmt_date(next(iter(targets)))}
    out_of_scope = [{"name": n, "basis": b, "moe": moe_applies(b)} for n, b in OUT_OF_SCOPE]
    # savings: how many entries carry a dollar estimate from a source
    est = [c["estimated_savings_usd"] for c in commitments if c["estimated_savings_usd"] is not None]
    savings = {"n_estimated": len(est), "total": sum(est) if est else None}
    # oversight committee
    members = [r for r in oversight if r["kind"] == "member"]
    seat_order = list(IOC_SEATS)
    members.sort(key=lambda m: (seat_order.index(m["seat"]), m["name"].split()[-1]))
    voting = [m for m in members if m["voting"]]
    committee = {
        "members": members,
        "voting": voting,
        "by_seat": {s: [m for m in voting if m["seat"] == s] for s in seat_order},
        "meetings": sorted((r for r in oversight if r["kind"] == "meeting"), key=lambda r: r["date"]),
        "findings": sorted((r for r in oversight if r["kind"] == "finding"), key=lambda r: r["adopted_on"]),
        "last_verified": max((r["status_as_of"] for r in oversight), default=None),
    }
    entry_agency = {c["id"]: AGENCIES[c["agency"]] for c in commitments}

    env = Environment(loader=FileSystemLoader(SITE / "templates"), autoescape=select_autoescape(enabled_extensions=("html.j2", "xml.j2"),
                                                    default_for_string=True),
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.filters["date"] = fmt_date
    env.filters["usd"] = fmt_usd
    env.globals.update(
        cfg=CFG, base=BASE, ver=static_version(), statuses=statuses, status_meta={status_key(k): v for k, v in STATUSES.items()},
        source_types=SOURCE_TYPES, categories=CATEGORIES, phases=PHASES, agencies=agencies,
        last_verified=last_verified, totals=totals, target=target, out_of_scope=out_of_scope, savings=savings, action_types=ACTION_TYPES, action_type_sources=ACTION_TYPE_SOURCES,
        kind_totals={k: sum(1 for c in commitments if c["action_type"] == k) for k in ACTION_TYPES},
        committee=committee, ioc_seats=IOC_SEATS, finding_bases=FINDING_BASES, n_total=len(commitments), build_date=datetime.date.today(),
        status_label=lambda s: STATUSES[None if s in (None, "unverified") else s]["label"],
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)

    try:
        og_ver = og.render(OUT / "og", agencies, f"maxmautner.com{BASE.rstrip('/')}", CFG["site_title"],
                           f"MTC target: {target['text']}" if target else "",
                           {status_key(k): v["label"] for k, v in STATUSES.items()})
    except OSError as e:  # fonts missing; pages still build, without preview images
        print(f"warning: preview images not rendered ({e})", file=sys.stderr)
        og_ver = {}
    env.globals["og_ver"] = og_ver

    def page(template, path, **ctx):
        dest = OUT / path / "index.html" if path else OUT / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(env.get_template(template).render(**ctx, current=path), encoding="utf-8")

    page("index.html.j2", "", milestones=milestones, next_deadline=nxt, ms_by_id=ms_by_id,
         next_milestone=next((m for m in milestones if not m.get("completed_on")), None))
    for a in agencies:
        page("agency.html.j2", a["slug"], agency=a, next_deadline=nxt)
    by_category = sorted(((cat, sum(1 for c in commitments if c["category"] == cat)) for cat in CATEGORIES),
                         key=lambda x: -x[1])
    page("how.html.j2", "how-it-works", by_category=[x for x in by_category if x[1]],
         ms_by_id=ms_by_id)
    page("oversight.html.j2", "oversight")
    page("methodology.html.j2", "methodology",
         n_commitments=len(commitments))
    page("changelog.html.j2", "changelog", history=history, entry_agency=entry_agency)

    (OUT / "changelog.xml").write_text(
        atom_feed(history, entry_agency, lambda k: STATUSES[k]["label"], datetime.date.today()), encoding="utf-8")

    # exports
    (OUT / "data" / "commitments.csv").write_text(to_csv(commitments, ms_by_id), encoding="utf-8")
    clean = [{k: v for k, v in c.items() if k in load_fields()} for c in commitments]
    (OUT / "data" / "commitments.json").write_text(
        json.dumps({"generated": str(datetime.date.today()), "commitments": clean},
                   indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    ms_clean = [{k: v for k, v in m.items() if k not in ("deadline_text",)} for m in milestones]
    (OUT / "data" / "oversight.json").write_text(
        json.dumps({"generated": str(datetime.date.today()), "records": oversight},
                   indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    (OUT / "data" / "milestones.json").write_text(
        json.dumps({"generated": str(datetime.date.today()), "milestones": ms_clean},
                   indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    shutil.copytree(SITE / "static", OUT / "static")
    if args.dev:
        write_dev_assets()
    src = ROOT / "sources"
    if src.exists():
        shutil.copytree(src, OUT / "sources", ignore=shutil.ignore_patterns(".*"))
    print(f"Built {len(commitments)} entries, {len(milestones)} milestones, "
          f"{len(history)} changelog commits -> {OUT.relative_to(ROOT)}/")


def load_fields():
    from scripts.schema import COMMITMENT_FIELDS
    return set(COMMITMENT_FIELDS)


if __name__ == "__main__":
    main()
