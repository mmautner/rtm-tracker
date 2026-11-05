# TODO: fields to verify or decide

Checked 2026-11-04. Each item names the entry or file it affects.

## Unverified entries (status is `null`)

- [ ] **`ac-transit-p1-scheduling-efficiencies`: the primary sources conflict.**
  - The AC Transit Board motion (Master Minute Order 26-209, June 10, 2026) added "adopting the
    schedule efficiencies study that benefits riders."
  - Staff Report 26-209 recommended *not* adopting the scheduling strategy.
  - MTC Res. 4743 (revised Aug. 26, 2026) does not list a scheduling strategy for AC Transit, and
    MTC's count of 29 adopted strategies appears to exclude it.
  - The motion's wording ("study that benefits riders") also differs from the report's ("examine
    schedules and adjust how operator shifts are structured… without affecting service").
  - **Next step:** ask AC Transit or MTC staff which is correct, or wait for MTC's next PIP update.

## Decisions for you

- [ ] **New status `not_adopted`** (not in your original list). It is used for 2 entries:
  `ac-transit-p1-retail-amenity-study` and `sfmta-p1-retail-amenity-study`. Both strategies were
  added by the IOC on May 22 and left out of the agencies' board actions. SB 63 lets agencies
  choose which strategies to adopt, so `missed` would overstate it and `not_started` would imply a
  commitment. To remove the status, delete it from `scripts/schema.py`.
- [ ] **New optional fields `target_completion` and `target_completion_basis`.** They hold MTC's
  "Estimated Completion Date: June 2029" for each adopted strategy (Res. 4743). This will be the
  natural date for judging `missed`. Keep or drop?
- [ ] **Candidate status changes, not applied** because each needs a judgment call on whether
  the source shows *this* strategy is in progress:
  - `bart-p1-shorter-trains`: BART's grand jury response (p. 22) cites a July 20, 2026 schedule
    change with "shorter midday Red trains, and some shorter Orange trains during the weekdays."
  - `bart-p1-parking-revenue`: MTC's May 27, 2026 release says BART's "new demand-based pricing for
    parking at select stations (effective July 1)" aligns with a Phase 1 strategy.
  - `bart-p1-speed-reliability`: BART's June 11 release mentions "schedule changes, such as the
    planned improvements in August 2026."
  - `sfmta-p1-fare-compliance-study`: MTC's May 27 release cites SFMTA's "Fares for our Future"
    initiative. The adopted strategy is a *study*, so this may not count.
- [ ] **Out-of-scope count.** You described "roughly 17" recipient agencies. SB 63 §67750(b)(2)-(16)
  names 15 direct recipients: 4 reviewed and 11 not (listed on the Methodology page). MTC's own
  programs, §67750(b)(10)-(12), are excluded.
- [ ] **Methodology commitments**, which the site states as policy:
  - monthly re-checks plus re-checks after relevant meetings
  - review of correction requests within five business days
  - "Who maintains this site" now names Max Mautner, says he supports transit and his essays take
    positions, and says the tracker takes no position on the measure. Confirm that wording.
- [ ] **Measure name.** MTC's Nov. 4 release calls it the "Regional Transit Measure (RTM)." The site
  title uses "Measure RTM." Confirm the ballot designation.

## Missing primary documents

- [ ] **Caltrain Resolution No. 2026-28** (June 4, 2026). The adoption is sourced to the minutes,
  the staff slides, and MTC Res. 4743, but the resolution text has not been found. The strategy
  wording in the slides differs slightly from the report.
- [ ] **BART Board minutes for June 11, 2026.** These were not in Legistar as of Nov. 4 (draft
  status). Adoption is sourced to the Executive Decision Document, BART's news release, BART's
  grand jury response, and MTC Res. 4743. The vote count is unknown.
- [ ] **BART grand jury response.** It is hosted on contracosta.courts.ca.gov, which is on the
  allowed-host list only for this document. Replace it with a bart.gov copy if one exists.
- [ ] **Election certification date.** When counties certify, set `completed_on` on
  `m-election-certified`. The Phase 2 deadline (480 days later) then appears automatically.

## Data notes, for your awareness

- **The AC Transit staff report seems to use a different version of the Phase 1 report.** It
  lists seven AC Transit strategies "(pages 49-52 of Attachment 1)," including "Direct customers
  to a single, regional trip-planning app," which the final May 27 report does not assign to AC
  Transit. No entry was created for it. The report's Attachment 1 on Legistar
  (actransit.legistar1.com/…/2e48dd90-….pdf) hasn't been compared with the final.
- **Table 25 of the report (p. 54)** labels "Examine schedules" and "Examine contracts" as
  Strategies for Future Consideration. The agency sections nonetheless list related Early Action
  Strategies (AC Transit scheduling; BART SFO lease and insurance/paratransit). They are tracked,
  and their notes say so.
- **Page numbers are PDF page numbers.** In MTC Res. 4743 they differ from the printed "Page X of
  22" (PDF p. 5 = printed p. 2).
- **The report's cover is dated May 22, 2026** (IOC adoption); the file was posted May 27. Source
  titles say "posted May 27, 2026."
- **No Phase 1 entry has a savings estimate**, because the report gives none per strategy.

## Setup

- [ ] **Review the wording of `site/templates/how.html.j2`.** It is prose, not data, so the validator
  can't check it. Re-read it when certification, Phase 2, or the oversight committee's
  implementation-plan requirements (§67766(c)(2)) change the picture.

- [ ] **Logos** in `site/static/logos/` came from each agency's website on 2026-11-05 (sources in
  `site/config.json` → `agency_logos`). BART's was cropped to the "ba" mark. AC Transit's is a 213×65
  PNG; swap in a vector version if one turns up.
- [ ] **Agency colors in `site/config.json` are approximate** (AC Transit green, BART blue, Caltrain
  red, Muni red). Check them against each agency's brand guide. Caltrain and Muni are both red; the
  agency name always appears next to the color, so the colors are never the only identifier.

- [ ] Create the GitHub repo `mmautner/rtm-tracker` (assumed in `site/config.json` → `repo_url`)
  and push. The changelog and the "view edit" links need it.
- [ ] Add `^rtm-tracker/` to `ignore_on_server` in the blog's `s3_website.yml` before the next
  blog deploy.
