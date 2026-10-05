# Index/crawl check — findings (2026-10-05)

Run from a GitHub Actions runner (public site, Googlebot user-agent). Raw CSVs in this folder.

## Passing
- **Site pages crawlable:** all 13,354 sitemap URLs checked against robots.txt; 0 blocked for Googlebot.
- **Site pages indexable:** 192 of 196 sampled sitemap pages return 200 with no noindex/nofollow.
- **Listing pages blocked:** 881 listing URLs found linked from site pages; all 881 blocked
  (`Disallow: /property-` 760, `Disallow: /*-listings` 121). None are in the sitemaps.

## To fix
1. **Retired pages still in the sitemaps.** 4 of 196 sampled sitemap URLs (~2%, so roughly 250-300
   site-wide) return HTTP 410 with `X-Robots-Tag: noindex, nofollow, noarchive`. All are
   `condos-for-sale-under-<price>-<place>` pages, e.g. `condos-for-sale-under-1-000-000-trianon-nc`.
   Googlebot spends crawls on these from the sitemap. Remove 410/noindex URLs from sitemap generation.
2. **robots.txt is 462 KB; Google ignores everything past 500 KiB.** ~9,300 rules, mostly one Disallow
   per retired page, duplicated in the `*` and `Googlebot` groups. Googlebot reads only its own group,
   which is the second half of the file, so its last rules are dropped first if the file grows ~8%.
   Replace per-page rules with patterns. If the per-page rules are for retired (410) pages, drop them:
   a 410 already tells Google the page is gone, and a Disallow stops Google from ever seeing that 410.
3. **Images blocked (minor):** 483 `/mlsphoto/` photos and a few `?v=` images on site pages
   (`/images/*.png`, hero `.webp`). Doesn't block indexing; keeps them out of Google Images.
4. **Rate limiting:** the site returned HTTP 429 to an unverified "Googlebot" after ~27 fast requests.
   Confirm in Search Console > Settings > Crawl stats > By response that real Googlebot gets no 429s.
