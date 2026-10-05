# Agent Results

Shared report file. Every agent appends its findings here when done.

## How to report

1. `git fetch origin claude/shared-agent-results-3seueh && git checkout claude/shared-agent-results-3seueh && git pull origin claude/shared-agent-results-3seueh`
2. Append a new section at the **bottom** of this file using the template below. Do not edit other agents' sections.
3. Commit, then push: `git push -u origin claude/shared-agent-results-3seueh`
4. If the push is rejected, run `git pull --rebase origin claude/shared-agent-results-3seueh`. On a conflict in this file, keep **both** sides (yours and the others'), then `git rebase --continue` and push again.

## Template

```
## <Agent name / task> — <YYYY-MM-DD HH:MM UTC>

**Task:** what you were asked to do
**Status:** done / partial / blocked

### Findings
- ...

### Links / files / PRs
- ...

### Open questions / next steps
- ...
```

---

<!-- Agent reports go below this line -->

## Codex / Combined HHR Google visibility investigation — 2026-10-05 18:25 UTC

**Task:** Combine the four requested investigations: site-wide indexing, crawl waste/competing identities, authority, and a ten-page diagnostic sample. Treat the owner's lack of backlinks as a known constraint.
**Status:** partial — read-only investigation completed with available evidence; OpenSEO access and several Google-specific checks remain blocked.

### Findings
- The strongest measured bottleneck is discovery/first-crawl coverage. The saved eligible-sitemap scope contains **12,542 URLs**, with **1,961 stored indexed/PASS results** and **7,878 discovered-not-indexed or unknown results**. These are rolling Google observations, not a fresh simultaneous count or the property-wide Search Console UI total. Most observations are older than two days.
- Full public sitemap traversal found **13 child sitemaps and 13,354 distinct URLs**. The saved eligibility model excludes **812** of those as not launched. At least one excluded sitemap URL, `condos-for-sale-under-1-000-000-28025-nc`, is live-proven HTTP 410. Classify all 812 before preparing a correction; do not release held pages to make the counts match.
- The saved topic family has a markedly lower indexing rate than the homes family. This favors investigating discovery paths and page-family value rather than assuming one site-wide metadata defect.
- A **49-URL stratified live sample** returned **47 HTTP 200s and two intentional HTTP 410s**. All 47 successful pages were self-canonical. Nine sampled eligible URLs with saved Google noindex results now serve indexable HTML. All five saved server-error URLs returned 200. These differences warrant fresh read-only inspection, not automatic robots or indexing changes.
- A locked noindex control still serves noindex. Preserve owner-held pages, OUTPUT-MASTER holds, LLM-only data-sheet exclusions, literal URLs, and approved direct-parent/direct-child links.
- No sampled anchors targeted the 812 excluded sitemap entries. This does not establish full-site reachability or absence of retired links.
- Saved verified crawler evidence shows substantial requests to retired destinations and assets, without recent 5xx/429 signals in the reviewed period. This supports an inventory review, but does not prove crawl-capacity exhaustion. Assets may be needed for rendering; query-variant waste remains unmeasured.
- Current sampled canonical delivery is consistent. Similar slugs and shared listings are not sufficient proof of equivalent intent. No consolidation, invented redirect target, or lateral link is proposed.
- The completed metadata repairs remain closed. Historical audit counts should not be reported as current defects.

The ten selected buyer-intent candidates span city, ZIP, neighborhood, NC/SC, property type, bedroom, price, and lifestyle intent. They are a diagnostic portfolio; search-demand forecasts and conversion values were unavailable, so this is not an objectively verified top-ten revenue list.

| Public page | Saved Google result | Main next check |
| --- | --- | --- |
| [Charlotte homes](https://www.helenharp-realty.com/homes-for-sale-charlotte-nc) | Indexed | Separate nonbrand query performance from aggregate page averages |
| [ZIP 28202 homes](https://www.helenharp-realty.com/homes-for-sale-28202-nc) | Indexed | Buyer-query relevance and useful local information |
| [Rock Hill new construction](https://www.helenharp-realty.com/new-construction-homes-for-sale-rock-hill-sc) | Indexed | Builder/community coverage and matched inventory scope |
| [Ballantyne Country Club townhomes](https://www.helenharp-realty.com/townhomes-for-sale-ballantyne-country-club-nc) | Indexed | Exact community scope and useful zero-listing state |
| [ZIP 28269 golf homes](https://www.helenharp-realty.com/golf-course-homes-28269-nc) | Indexed | Repeated noun in live title; golf adjacency versus membership |
| [Davis Ridge homes](https://www.helenharp-realty.com/homes-for-sale-davis-ridge-nc) | Indexed | Query relevance and neighborhood-specific value |
| [The Peninsula homes](https://www.helenharp-realty.com/homes-for-sale-the-peninsula-nc) | Historical noindex | Current live HTML is indexable; refresh inspection and compare crawl dates |
| [Ayrsley Townhomes](https://www.helenharp-realty.com/homes-for-sale-ayrsley-townhomes-nc) | Crawled, not indexed | Exact community intent, focused buyer guidance, approved incoming parent edge |
| [One-bedroom 28202 condos](https://www.helenharp-realty.com/1-bedroom-condos-for-sale-28202-nc) | Discovered, not indexed | Approved discovery path; section headings incorrectly use the search phrase as a geographic name |
| [28210 condos under $300k](https://www.helenharp-realty.com/condos-for-sale-under-300-000-28210-nc) | Indexed | Price-filter accuracy and distinct purpose versus broader condo pages |

Some indexed pages have impressions and weak buyer-query performance; indexing alone will not produce traffic. GSC average position is not an exact current ranking. Large HTML/text output merits focus and rendering review, but word count alone does not establish poor quality.

**Authority:** No backlinks is a plausible contributor to low crawl demand and weak rankings, not a proven explanation for all exclusions. Seven of these ten pages have stored indexed results. Relevant earned links are worth pursuing for checked original resources, such as a source-linked development digest, condo HOA/total-cost guide, or reproducible local inventory study. Candidate prospect classes include local housing reporters, relevant neighborhood associations, and legitimate membership directories. No outreach or paid links occurred.

Free searches identified local specialists alongside portals, including Uphomes, Palmetto Park, Explore Cornelius Homes, GolfHomes, and Houses in Charlotte. These are candidate competitors, not verified current Google winners; referring-domain comparisons and exact Google SERPs remain unavailable.

### Links / files / PRs
- [Google crawl-demand and capacity guidance](https://developers.google.com/crawling/docs/crawl-budget)
- [Google crawling, indexing and serving explanation](https://developers.google.com/search/docs/fundamentals/how-search-works)
- [Google Indexing API supported page types](https://developers.google.com/search/apis/indexing-api/v3/using-api): accepted real-estate URL submissions do not establish indexing or a supported guaranteed accelerator.
- A detailed local report, ten-page evidence CSV, findings CSV, reproducible sampler and complete PowerShell recheck script were prepared. They are not shared-repo artifacts in this update.
- PowerShell syntax parsing and Python compilation passed; CSV counts and coverage arithmetic passed. The PowerShell script was not run end-to-end.
- No PR, production edit, sitemap/indexing submission, backlink outreach or paid research was performed.

### Open questions / next steps
1. Reconcile the 812 excluded sitemap entries with current retirements and holds, then prepare a publication diff.
2. Refresh Google observations for historical noindex/server-error results; preserve intentional policies.
3. Prove approved discovery paths for the discovered/unknown queue, prioritizing topic families.
4. Review post-crawl nonindexed pages and the concrete geo-context defect; consolidate only after equivalence is proven.
5. Develop a few checked original resources suitable for relevant earned links.
6. Obtain OpenSEO access to project `d7912473-3174-40c0-841d-483dc14db74d`. No OpenSEO tools were exposed and plugin search found no entry, so shared context, saved OpenSEO reports, paid pricing and an OpenSEO-hosted report remain unavailable. Paid calls made: zero.
7. Complete the approved canonical inventory outside the sitemap, publication-cohort export, full emitted-link graph, parameter-aware raw-log audit, browser rendering and fresh Google inspections. The owner's approximately 30,000 intended pages cannot yet be reconciled to a complete approved public inventory.
