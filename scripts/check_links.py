"""Check every source URL in data/*.yaml.

    .venv/bin/python scripts/check_links.py                 # report only
    .venv/bin/python scripts/check_links.py --open-issues   # also open GitHub issues (needs gh + GH_TOKEN)

A link counts as broken on 404/410, other 4xx except 401/403/429, 5xx on two tries, or a
connection/DNS/TLS failure. 401/403/429 are reported as "inconclusive" without opening an
issue: some government sites (leginfo, for one) refuse all automated requests even when
the page works in a browser.

Opens at most one issue per broken URL; an issue that is already open is left alone.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "site" / "config.json").read_text())
UA = f"rtm-tracker-linkcheck (+{CFG['repo_url']})"
INCONCLUSIVE = {401, 403, 429}
LABEL = "broken-link"


def collect():
    urls = {}
    for c in yaml.safe_load((ROOT / "data" / "commitments.yaml").read_text()) or []:
        for s in c.get("sources") or []:
            urls.setdefault(s["url"], set()).add(c["id"])
    for m in yaml.safe_load((ROOT / "data" / "milestones.yaml").read_text()) or []:
        for s in m.get("sources") or []:
            urls.setdefault(s["url"], set()).add(m["id"])
        for e in m.get("estimates") or []:
            if e.get("source"):
                urls.setdefault(e["source"]["url"], set()).add(m["id"])
    return urls


def fetch(url, method):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:  # DNS, TLS, timeout, connection reset
        return None, f"{type(e).__name__}: {e}"


def check(url):
    status, err = fetch(url, "HEAD")
    if status in (405, 501) or (status and status >= 400 and status not in INCONCLUSIVE):
        status, err = fetch(url, "GET")  # some servers reject HEAD
    if status is None or status >= 500:
        time.sleep(5)
        status, err = fetch(url, "GET")
    if status is not None and status < 400:
        return "ok", status, None
    if status in INCONCLUSIVE:
        return "inconclusive", status, None
    return "broken", status, err


def open_issue(url, used_by, status, err):
    title = f"Broken source link: {url}"[:250]
    existing = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--label", LABEL, "--limit", "200", "--json", "title"],
        capture_output=True, text=True, check=True).stdout
    if any(i["title"] == title for i in json.loads(existing or "[]")):
        print(f"  issue already open for {url}")
        return
    body = (f"The weekly link check could not load this source.\n\n"
            f"- URL: {url}\n- Result: {status or err}\n"
            f"- Used by: {', '.join('`'+i+'`' for i in sorted(used_by))}\n\n"
            "Find the document's new location (or an archived copy on the same agency's site), "
            "update the `url` in `data/`, and close this issue.")
    subprocess.run(["gh", "label", "create", LABEL, "--color", "B60205", "--force",
                    "--description", "A source URL in data/ no longer loads"], capture_output=True)
    subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", LABEL], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-issues", action="store_true")
    args = ap.parse_args()
    urls = collect()
    results = {"ok": [], "inconclusive": [], "broken": []}
    for url, used_by in sorted(urls.items()):
        kind, status, err = check(url)
        results[kind].append((url, used_by, status, err))
        print(f"{kind:12} {status or err}  {url}")
    print(f"\n{len(results['ok'])} ok, {len(results['inconclusive'])} inconclusive, "
          f"{len(results['broken'])} broken (of {len(urls)} unique URLs)")
    if args.open_issues:
        for url, used_by, status, err in results["broken"]:
            open_issue(url, used_by, status, err)
    summary = Path(__import__("os").environ.get("GITHUB_STEP_SUMMARY", "/dev/null"))
    with open(summary, "a") as f:
        f.write(f"### Link check\n\n{len(results['ok'])} ok · {len(results['inconclusive'])} inconclusive · "
                f"{len(results['broken'])} broken\n\n")
        for kind in ("broken", "inconclusive"):
            for url, _, status, err in results[kind]:
                f.write(f"- **{kind}** ({status or err}): {url}\n")
    sys.exit(1 if results["broken"] else 0)


if __name__ == "__main__":
    main()
