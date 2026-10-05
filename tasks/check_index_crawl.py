#!/usr/bin/env python3
"""Verify crawl/index directives for helenharp-realty.com.

Goal being checked:
  * Site pages (everything in the sitemaps) must be crawlable by Googlebot
    (not blocked by robots.txt) and indexable (no noindex/nofollow in a meta
    tag or X-Robots-Tag header).
  * Listing pages must be blocked by robots.txt, so Googlebot never requests them.
  * Sitemaps must not contain listing URLs.
  * robots.txt must not block CSS/JS/images that site pages need to render.

Read-only: it only sends GET requests. Python 3.8+, standard library only.

Usage:
  python check_index_crawl.py
  python check_index_crawl.py --listing-pattern "/listing/"     # regex on path
  python check_index_crawl.py --sample 500 --out results
"""
import argparse
import collections
import csv
import gzip
import io
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip" or url.endswith(".gz"):
                try:
                    body = gzip.decompress(body)
                except OSError:
                    pass
            return r.status, r.geturl(), dict(r.headers), body
    except urllib.error.HTTPError as e:
        return e.code, url, dict(e.headers or {}), b""
    except Exception as e:  # network error
        return None, url, {"error": str(e)}, b""


# ---------------------------------------------------------------- robots.txt
class Robots:
    """Google-style robots.txt matching: longest rule wins, Allow wins ties,
    '*' wildcard and '$' end anchor supported."""

    def __init__(self, text):
        self.sitemaps = []
        groups = []  # list of (agents, rules)
        agents, rules, in_rules = [], [], False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, val = (s.strip() for s in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if in_rules:
                    groups.append((agents, rules))
                    agents, rules, in_rules = [], [], False
                agents.append(val.lower())
            elif key in ("allow", "disallow"):
                in_rules = True
                if val:
                    rules.append((key == "allow", val))
            elif key == "sitemap":
                self.sitemaps.append(val)
        if agents:
            groups.append((agents, rules))
        specific = [r for a, r in groups if "googlebot" in a]
        fallback = [r for a, r in groups if "*" in a]
        chosen = specific or fallback
        self.group = "googlebot" if specific else ("*" if fallback else "none")
        self.rules = [rule for rs in chosen for rule in rs]
        self._compiled = [(allow, pat, self._regex(pat)) for allow, pat in self.rules]

    @staticmethod
    def _regex(pat):
        anchored = pat.endswith("$")
        body = re.escape(pat[:-1] if anchored else pat).replace(r"\*", ".*")
        return re.compile("^" + body + ("$" if anchored else ""))

    def verdict(self, url):
        """Return (allowed, matching_rule_or_empty)."""
        p = urllib.parse.urlsplit(url)
        path = (p.path or "/") + (("?" + p.query) if p.query else "")
        best = None
        for allow, pat, rx in self._compiled:
            if rx.match(path):
                key = (len(pat), allow)
                if best is None or key > best[0]:
                    best = (key, allow, pat)
        if best is None:
            return True, ""
        return best[1], ("Allow: " if best[1] else "Disallow: ") + best[2]


# ---------------------------------------------------------------- sitemaps
def localname(tag):
    return tag.rsplit("}", 1)[-1]


def read_sitemaps(roots):
    """Return {url: sitemap_file} for every <loc> in every child sitemap."""
    urls, seen, queue = {}, set(), list(roots)
    while queue:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        status, _, _, body = fetch(sm)
        if status != 200 or not body:
            print(f"  ! sitemap {sm} -> HTTP {status}")
            continue
        try:
            root = ET.fromstring(body)
        except ET.ParseError as e:
            print(f"  ! sitemap {sm} unparseable: {e}")
            continue
        kind = localname(root.tag)
        for loc in root.iter():
            if localname(loc.tag) == "loc" and loc.text:
                u = loc.text.strip()
                if kind == "sitemapindex":
                    queue.append(u)
                else:
                    urls.setdefault(u, sm)
    return urls, sorted(seen)


# ---------------------------------------------------------------- page parsing
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta_robots, self.canonical = [], ""
        self.links, self.assets = set(), set()

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta" and a.get("name", "").lower() in ("robots", "googlebot"):
            self.meta_robots.append(f'{a["name"].lower()}={a.get("content", "")}')
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = a.get("href", "")
            elif "stylesheet" in rel or "preload" in rel:
                if a.get("href"):
                    self.assets.add(a["href"])
        elif tag == "a" and a.get("href"):
            self.links.add(a["href"])
        elif tag in ("script", "img") and a.get("src"):
            self.assets.add(a["src"])


def directives(headers, meta_list):
    """Lower-cased directives Googlebot would apply (header + meta)."""
    found = []
    for k, v in headers.items():
        if k.lower() == "x-robots-tag":
            # 'googlebot: noindex' or plain 'noindex'; ignore other bots
            if ":" in v and not v.lower().startswith(("googlebot", "unavailable_after")):
                continue
            found.append(v.lower())
    for m in meta_list:
        found.append(m.split("=", 1)[1].lower())
    joined = ",".join(found)
    return {d.strip() for d in re.split(r"[,:]", joined) if d.strip()}


def inspect(url, host):
    status, final, headers, body = fetch(url)
    p = PageParser()
    if body and "html" in headers.get("Content-Type", headers.get("content-type", "html")):
        try:
            p.feed(body.decode("utf-8", "replace"))
        except Exception:
            pass
    d = directives(headers, p.meta_robots)
    same = lambda h: urllib.parse.urljoin(final, h)
    links = {urllib.parse.urldefrag(same(h))[0] for h in p.links}
    links = {u for u in links if urllib.parse.urlsplit(u).netloc == host}
    assets = {same(h) for h in p.assets}
    assets = {u for u in assets if urllib.parse.urlsplit(u).netloc == host}
    xrt = "; ".join(v for k, v in headers.items() if k.lower() == "x-robots-tag")
    time.sleep(0.25)
    return {
        "url": url, "status": status, "final_url": final,
        "x_robots_tag": xrt, "meta_robots": " | ".join(p.meta_robots),
        "noindex": "noindex" in d or "none" in d,
        "nofollow": "nofollow" in d or "none" in d,
        "canonical": p.canonical, "_links": links, "_assets": assets,
    }


def path_shape(url):
    """Group URLs into a pattern like /listing/{id} for reporting."""
    segs = [s for s in urllib.parse.urlsplit(url).path.split("/") if s]
    out = []
    for s in segs[:3]:
        if re.fullmatch(r"\d+", s):
            out.append("{n}")
        elif re.search(r"\d{5,}", s):
            out.append(re.sub(r"\d{5,}", "{n}", s)[:40])
        else:
            out.append(s if len(segs) == 1 else s[:40])
    return "/" + "/".join(out) + ("/..." if len(segs) > 3 else "")


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="https://www.helenharp-realty.com")
    ap.add_argument("--listing-pattern", default="",
                    help="regex matched against the URL path that identifies listing pages")
    ap.add_argument("--sample", type=int, default=300, help="site pages to fetch")
    ap.add_argument("--listing-sample", type=int, default=60, help="listing pages to fetch")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="index_crawl_results")
    args = ap.parse_args()

    site = args.site.rstrip("/")
    host = urllib.parse.urlsplit(site).netloc
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    random.seed(1)
    fails, notes = [], []

    # 1. robots.txt
    print("[1] robots.txt")
    status, _, _, body = fetch(site + "/robots.txt")
    if status != 200:
        print(f"  robots.txt HTTP {status} - cannot continue")
        sys.exit(2)
    robots_text = body.decode("utf-8", "replace")
    (out / "robots.txt").write_text(robots_text, encoding="utf-8")
    robots = Robots(robots_text)
    print(f"  group applied to Googlebot: {robots.group}; {len(robots.rules)} rules")
    for allow, pat in robots.rules:
        print(f"    {'Allow' if allow else 'Disallow'}: {pat}")

    # 2. sitemaps = the site pages
    print("[2] sitemaps")
    sitemap_urls, files = read_sitemaps(robots.sitemaps or [site + "/sitemap.xml"])
    print(f"  {len(files)} sitemap files, {len(sitemap_urls)} URLs")

    # 3. robots verdict for EVERY sitemap URL (no fetching needed)
    print("[3] robots.txt verdict on every sitemap URL")
    blocked_site = []
    for u, sm in sitemap_urls.items():
        ok, rule = robots.verdict(u)
        if not ok:
            blocked_site.append({"url": u, "sitemap": sm, "rule": rule})
    write_csv(out / "site_pages_blocked_by_robots.csv", blocked_site, ["url", "sitemap", "rule"])
    print(f"  blocked: {len(blocked_site)}")
    if blocked_site:
        fails.append(f"{len(blocked_site)} sitemap (site) URLs are BLOCKED by robots.txt "
                     f"-> site_pages_blocked_by_robots.csv")

    listing_rx = re.compile(args.listing_pattern) if args.listing_pattern else None
    if listing_rx:
        in_sm = [u for u in sitemap_urls if listing_rx.search(urllib.parse.urlsplit(u).path)]
        if in_sm:
            fails.append(f"{len(in_sm)} listing-pattern URLs are IN the sitemaps "
                         f"(e.g. {in_sm[0]})")

    # 4. fetch a stratified sample of site pages
    by_file = collections.defaultdict(list)
    for u, sm in sitemap_urls.items():
        by_file[sm].append(u)
    per = max(1, args.sample // max(1, len(by_file)))
    sample = [u for us in by_file.values() for u in random.sample(us, min(per, len(us)))]
    sample.insert(0, site + "/")
    print(f"[4] fetching {len(sample)} site pages (stratified across sitemap files)")
    with ThreadPoolExecutor(args.workers) as ex:
        site_rows = list(ex.map(lambda u: inspect(u, host), sample))
    bad_site = [r for r in site_rows if r["status"] != 200 or r["noindex"] or r["nofollow"]]
    cols = ["url", "status", "final_url", "noindex", "nofollow", "meta_robots",
            "x_robots_tag", "canonical"]
    write_csv(out / "site_pages_sample.csv", site_rows, cols)
    write_csv(out / "site_pages_problems.csv", bad_site, cols)
    ni = sum(r["noindex"] for r in site_rows)
    nf = sum(r["nofollow"] for r in site_rows)
    non200 = sum(r["status"] != 200 for r in site_rows)
    print(f"  noindex: {ni}  nofollow: {nf}  non-200: {non200}")
    if ni or nf:
        fails.append(f"{ni} sampled site pages carry noindex, {nf} carry nofollow "
                     f"-> site_pages_problems.csv")
    if non200:
        notes.append(f"{non200} sampled site pages not HTTP 200 (see site_pages_problems.csv; "
                     f"410s may be intentional retirements)")

    # 5. listing pages: linked from site pages but not in the sitemaps
    print("[5] listing pages")
    sm_set = set(sitemap_urls)
    linked = set().union(*(r["_links"] for r in site_rows)) if site_rows else set()
    off_sitemap = sorted(u for u in linked if u not in sm_set and u.rstrip("/") != site)
    if listing_rx:
        listings = [u for u in off_sitemap if listing_rx.search(urllib.parse.urlsplit(u).path)]
    else:
        listings = off_sitemap
    shapes = collections.Counter(path_shape(u) for u in off_sitemap)
    with open(out / "linked_not_in_sitemap_by_pattern.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pattern", "count", "robots_allowed", "example"])
        for shape, n in shapes.most_common():
            ex_urls = [u for u in off_sitemap if path_shape(u) == shape]
            allowed = sum(robots.verdict(u)[0] for u in ex_urls)
            w.writerow([shape, n, allowed, ex_urls[0]])
    print(f"  {len(off_sitemap)} internal URLs linked from site pages but not in sitemaps, "
          f"{len(shapes)} patterns (linked_not_in_sitemap_by_pattern.csv)")
    if not listing_rx:
        notes.append("No --listing-pattern given: every linked URL not in the sitemaps was "
                     "treated as a listing candidate. Review linked_not_in_sitemap_by_pattern.csv, "
                     "then re-run with --listing-pattern for an exact verdict.")

    listing_rows = []
    for u in listings:
        ok, rule = robots.verdict(u)
        listing_rows.append({"url": u, "robots_allowed": ok, "rule": rule})
    open_listings = [r for r in listing_rows if r["robots_allowed"]]
    write_csv(out / "listing_pages_robots.csv", listing_rows, ["url", "robots_allowed", "rule"])
    print(f"  listing candidates: {len(listing_rows)}  still crawlable: {len(open_listings)}")
    if open_listings:
        fails.append(f"{len(open_listings)} listing(-candidate) URLs are NOT blocked by "
                     f"robots.txt -> listing_pages_robots.csv (filter robots_allowed=True)")

    # what those pages serve if fetched anyway (Google won't see this when blocked)
    ls = random.sample(listings, min(args.listing_sample, len(listings)))
    with ThreadPoolExecutor(args.workers) as ex:
        lrows = list(ex.map(lambda u: inspect(u, host), ls))
    for r in lrows:
        r["robots_allowed"] = robots.verdict(r["url"])[0]
    write_csv(out / "listing_pages_sample.csv", lrows, ["robots_allowed"] + cols)

    # 6. assets needed to render site pages must not be blocked
    print("[6] render assets")
    assets = set().union(*(r["_assets"] for r in site_rows)) if site_rows else set()
    blocked_assets = [{"url": a, "rule": robots.verdict(a)[1]} for a in sorted(assets)
                      if not robots.verdict(a)[0]]
    write_csv(out / "assets_blocked_by_robots.csv", blocked_assets, ["url", "rule"])
    print(f"  {len(assets)} same-host assets, blocked: {len(blocked_assets)}")
    if blocked_assets:
        fails.append(f"{len(blocked_assets)} CSS/JS/image files used by site pages are blocked "
                     f"-> assets_blocked_by_robots.csv")

    # summary
    lines = [
        "# Index / crawl directive check", "",
        f"Site: {site}  ",
        f"Run: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}  ",
        f"robots.txt group for Googlebot: `{robots.group}` ({len(robots.rules)} rules)  ",
        f"Sitemap URLs (site pages): {len(sitemap_urls)} - all checked against robots.txt  ",
        f"Site pages fetched: {len(site_rows)}  ",
        f"Listing candidates: {len(listing_rows)} (pattern: `{args.listing_pattern or 'auto'}`)", "",
        "## Result: " + ("FAIL" if fails else "PASS"), "",
    ]
    lines += [f"- FAIL: {f}" for f in fails] or ["- Site pages crawlable+indexable, listing pages blocked."]
    lines += [f"- NOTE: {n}" for n in notes]
    lines += ["", "## robots.txt rules applied to Googlebot", "```"]
    lines += [f"{'Allow' if a else 'Disallow'}: {p}" for a, p in robots.rules] + ["```"]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
