# Decisions

- **Python + Jinja2, not Eleventy.** Same toolchain as the sibling sites; two dependencies.
- **Deploy with `deploy.sh` to S3/CloudFront at maxmautner.com/rtm-tracker/**, like the siblings
  (chosen over GitHub Pages, 2026-11-04). GitHub Actions validates and builds on every push, but
  doesn't publish.
- **No Google Analytics**, unlike the siblings: the spec rules out tracking scripts.
- **One entry per recommended action** in the report's agency sections (35), not per strategy
  heading as MTC counts them (32). The Methodology page explains the difference.
- **`status: null` displays as "Unverified"** rather than "Not started," so the site never states a
  status it has no source for.
- **Added `not_adopted`** for strategies a board left out of its July 1 action (see TODO.md).
- **Added categories `revenue` and `ridership/customer experience`**, the report's own groupings
  (approved 2026-11-04).
- **Milestone deadlines are rules** ("480 days after certification") and become dates when the
  anchor milestone is completed. Agency and MTC timing claims are shown as labeled estimates.
- **The validator restricts source URLs to a host allowlist** (`site/config.json`), which makes the
  primary-source rule mechanical.
- **`deploy.sh` refuses to publish uncommitted data**, so every published status is in the
  changelog.
- **The link checker treats 401/403/429 as inconclusive**, since leginfo blocks all bots.
- **Styled like maxmautner.com and the sibling sites** (2026-11-05): the blog's header, dark/light
  toggle, Newsreader + IBM Plex Sans, and warm tokens. `site/static/rtm.css` loads before the blog's
  `/assets/css/site.css`, and its rules are all `.rt-*`, the same arrangement as `crashes.css` and
  `speeds.css`. Fonts come from the blog's self-hosted `/resources/fonts/`, not Google Fonts, so a page
  makes no third-party requests.
- **Status colors use the blog's amber accent**, getting stronger from adopted to implemented. "Missed"
  is solid text color, as prominent as "implemented" and not red, so it can't be confused with an
  agency's color.
- **Agency brand colors and logos, for identification only.** Colors appear as wayfinding stripes and
  dots (`agency_colors`) and never encode data. Official logos (`agency_logos`, downloaded 2026-11-05
  from each agency's site) appear small on the scorecard cards and agency headings, on a light tile so
  they read in dark mode; Muni's white worm sits on its red. Not in the tab bar (illegible at that size)
  and not in link-preview images, where the "not affiliated" disclaimer isn't visible and an image could
  pass for an official one. The footer says the site isn't affiliated with or endorsed by any agency.
- **"How it works" page** (2026-11-05) explains the review, the commitments, Phase 2, implementation
  plans, and the funding condition for first-time visitors, with every sentence cited to a page of
  the statute or the Phase 1 report. The home page shows the same five steps compactly; which steps
  are "done" and "up next" comes from `data/milestones.yaml`, so it updates without editing templates.
- **Link previews, feed, context, and maintainer** (2026-11-05):
  - `og/index.png` and `og/<agency>.png` are drawn by `scripts/og.py` during the build from the same
    numbers as the pages, with a content hash in the `og:image` URL so social sites refetch on change.
    The agency image spells out every non-zero status so nothing in its bar is unlabeled.
  - `changelog.xml` is an Atom feed built from the same git history as the changelog page.
  - MTC's June 2029 target appears next to "Implemented" wherever the counts appear, but only while
    every adopted entry has the same target, so the summary never hides a difference.
  - The maintainer is named on every page. The tracker states it takes no position on the measure.
- **"Don't see your agency?"** sits under the scorecard. It lists the 11 recipients outside the
  review and marks those subject to maintenance of effort (§67770 covers §67750(b)(2)-(9)).
- **Templates are autoescaped.** `select_autoescape()` keys off the file extension, and `*.html.j2`
  didn't match, so escaping was off until 2026-11-05.
- **Agencies are listed by annual ridership, FY 2024-25** (Muni, BART, AC Transit, Caltrain), from the Phase 1 report's agency profiles (pp. 38, 24, 17, 32), on every page and in the overview preview image (2026-11-05). Sentences that paraphrase the statute keep its order (AC Transit, BART, Caltrain, Muni).
