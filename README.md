# Measure RTM Efficiency Tracker

A static site that tracks whether Muni (SFMTA), BART, AC Transit, and Caltrain carry out the
cost-saving commitments required by California SB 63 (Gov. Code §67760-67766). Every page is
generated from two YAML files; you never edit HTML to update the tracker.

Published at `https://maxmautner.com/rtm-tracker/` (S3 + CloudFront, same setup as
`san-mateo-crashes` and `san-mateo-speeds`).

## Update an entry (about 5 minutes)

1. Open `data/commitments.yaml` and find the entry by its `id`. Every id is shown at the bottom of
   the expanded entry on the site, for example `bart-p1-parking-revenue`.
2. Change what the new source supports, and nothing else:
   - `status`: one of `null`, `not_adopted`, `not_started`, `adopted`, `in_progress`, `implemented`,
     `missed`, `superseded`. Definitions are on the Methodology page and in `scripts/schema.py`.
   - `status_as_of`: today's date, `YYYY-MM-DD`. Update it even if the status didn't change; it is
     the "last verified" date shown on the site.
   - `sources`: add the document that supports the change:
     ```yaml
     - title: "SFMTA Board of Directors Resolution No. 261103-101 (Nov. 3, 2026)"
       url: https://www.sfmta.com/media/12345/download
       page: 2          # PDF page; use null for a web page
       type: board_item # statute | report | board_item | news_release | agency_document
     ```
   - `notes`: one or two plain sentences on what changed and why. Quote the source when you can.
3. Check and preview:
   ```sh
   .venv/bin/python scripts/validate.py
   .venv/bin/python build_site.py --dev && .venv/bin/python -m http.server -d dist 8765
   # open http://127.0.0.1:8765/rtm-tracker/
   ```
4. Commit with a message that says what changed. The message becomes the changelog heading:
   ```sh
   git commit -am "BART parking revenue: in progress (demand-based pricing in effect, Nov. 3 board item)"
   git push
   ```
5. Publish: `./deploy.sh` (use `./deploy.sh --dry-run` first to see what would upload).

### Kind of commitment

Every entry has `action_type` (`action`, `study`, or `advocacy`) and `action_type_basis`, the words
from the recommendation it was classified from. The rule is in `scripts/schema.py` (`ACTION_TYPES`)
and on the Methodology page. When adding an entry, copy the deciding verb phrase exactly; the
validator rejects a basis that doesn't appear in the recommendation.

### Rules the validator enforces

- Every entry has at least one source with a URL, a page (or `null`), and a type.
- Source URLs must be on a primary-source host listed in `site/config.json`
  (`primary_source_hosts`). Add a host there only if it is MTC, one of the agencies, or the
  Legislature.
- Any status other than `null` needs a `board_action` and a source other than the review report.
- `status` must be one of the allowed values; dates must be real dates, and `status_as_of` can't
  be in the future.

### Rules the validator can't enforce

- Don't infer a status. If sources conflict or are unclear, set `status: null` and describe the
  conflict in `notes`.
- Don't enter a dollar figure or date that isn't in a source.
- Record misses as plainly as passes.

## Add an entry

Copy an existing entry for the same agency and change every field. Pick a new `id` in the form
`<agency-slug>-<phase>-<short-name>`, e.g. `bart-p2-paratransit-contract`. For Phase 2 entries
use `phase: 2`; for implementation-plan commitments use `phase: implementation_plan`. Set
`required_by` to a milestone id from `data/milestones.yaml` or to a date.

## Oversight records

`data/oversight.yaml` holds three kinds of record, each with sources like any entry:

- `member`: one per committee member. Update when MTC's roster changes; set `status_as_of`.
- `meeting`: one per committee meeting, with actions and the vote record once minutes are approved.
- `finding`: one per written finding an agency adopts to reject a committee recommendation
  (§67766(f)(3)). Copy the template at the bottom of the file. Record `expires_on` (12 months unless
  renewed), `renewed_on`, and the date of MTC's notice to the Legislature.

## Update a milestone

Edit `data/milestones.yaml`. A milestone with a `deadline_rule` ("N days after milestone X") gets a
real date as soon as X has a `completed_on` date. For example, when the election results are
certified, set `completed_on` on `m-election-certified`, and the Phase 2 deadline (480 days later)
appears on the site.

## Files

```
data/commitments.yaml       all tracked recommendations (edit this)
data/milestones.yaml        statutory deadlines (edit this)
data/oversight.yaml         oversight committee members and meetings; findings rejecting its recommendations (edit this)
site/config.json            site settings, contact, allowed source hosts, deploy target
site/templates/*.j2         page templates (Jinja2)
site/static/                CSS and two small scripts (filters, print expansion)
scripts/schema.py           allowed values and status definitions (shared by validator and site)
scripts/validate.py         data checks; run in CI and by the build
scripts/changelog.py        builds the changelog from git history of data/
scripts/check_links.py      weekly link check; opens an issue per broken URL
scripts/og.py               link-preview images (og/*.png), drawn from the same numbers as the pages
site/og/fonts/              Newsreader and IBM Plex Sans for the preview images (SIL OFL)
build_site.py               writes dist/rtm-tracker/: pages, CSV/JSON exports, changelog.xml feed, preview images
deploy.sh                   validate, build, and upload to S3; invalidate CloudFront
sources/                    local copies of source documents (SB 63 chaptered text)
TODO.md                     fields that still need verification
```

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Automation

- `.github/workflows/build.yml` runs on every push and pull request: validates the data and builds
  the site (with full git history, for the changelog). A bad entry fails the check.
- `.github/workflows/linkcheck.yml` runs every Monday. It opens one issue (label `broken-link`)
  per source URL that returns 404/410/5xx or fails to connect. 401/403/429 are reported as
  inconclusive without an issue, because some government sites block automated requests;
  leginfo.legislature.ca.gov always does.

## Deploying

`./deploy.sh` refuses to run if `data/` has uncommitted changes, so everything published is in
the changelog. It writes only under `s3://maxmautner.com/rtm-tracker/`.

**The blog's deploy must leave this prefix alone.** In the blog repo's `s3_website.yml`,
`ignore_on_server` should list `^rtm-tracker/`, as it does for the other two sites.
