# Codex task: verify index/crawl settings on helenharp-realty.com

**Read-only. Do not change the site, robots.txt, sitemaps, or Search Console.**

## What the owner set today
All listing pages were set to noindex/nofollow and blocked in robots.txt.

## What must be true (verify each)
1. **Site pages** (everything in the sitemaps) are crawlable: robots.txt does not block them.
2. **Site pages** are indexable: no `noindex` / `nofollow` / `none` in a meta robots tag,
   meta googlebot tag, or `X-Robots-Tag` header, and they return HTTP 200.
3. **Listing pages** are blocked by robots.txt for Googlebot (so Googlebot never requests them).
   Whether they also carry noindex does not matter once blocked, because Google never sees it.
4. **No listing URLs are in the sitemaps.**
5. robots.txt does not block CSS/JS/images that site pages need to render.

## How
1. Run from the repo root (Python 3.8+, no installs needed):
   ```
   python tasks/check_index_crawl.py
   ```
   With no pattern, every internal URL linked from site pages but missing from the sitemaps is
   treated as a listing candidate. Open `index_crawl_results/linked_not_in_sitemap_by_pattern.csv`
   and identify which URL pattern is the listing pages.
2. Re-run with that pattern (a regex matched against the URL path), for example:
   ```
   python tasks/check_index_crawl.py --listing-pattern "^/listing/"
   ```
   Confirm the pattern by opening two or three of those URLs in a browser: they must be
   individual property listings, and no site/hub page may match the pattern.
3. Optional, larger sample: `--sample 1000`.

The script checks robots.txt against **every** sitemap URL (no fetch needed), fetches a
stratified sample of site pages for meta/header directives, and checks every listing URL
it finds linked from those pages. Exit code 0 = PASS, 1 = FAIL.

## Report back
Append a section to `AGENT_RESULTS.md` following the instructions at the top of that file. Include:
- PASS/FAIL for each of checks 1-5, with counts
- The exact robots.txt rules that apply to Googlebot (from `SUMMARY.md`)
- The listing pattern used and how you confirmed it
- For any FAIL: the example URLs and the robots.txt rule or tag responsible, plus the exact
  fix (proposed only, not applied)
