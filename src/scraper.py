# src/scraper.py
import requests
import time
import json
import logging
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse

# --- Config ---
BASE_URL = "https://www.t-nation.com"
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "tnation_articles.json")
DEBUG_PREFIX = os.path.join(DATA_DIR, "debug_")
# regex to match article URLs like /t/slug/12345 or full URLs
ARTICLE_RE = re.compile(r'(?:/t/[^/]+/\d+|https?://(?:www\.)?t-nation\.com/t/[^/]+/\d+)', re.IGNORECASE)

# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("tnation_scraper.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class TNationScraper:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        os.makedirs(DATA_DIR, exist_ok=True)

    def fetch(self, url, timeout=15, retries=3):
        for attempt in range(retries):
            try:
                logger.info(f"GET {url} (attempt {attempt+1})")
                r = self.session.get(url, timeout=timeout)
                logger.info(f" -> status {r.status_code} for {url}")
                if r.status_code == 200:
                    return r
                if r.status_code in (403, 429):
                    wait = 2 ** attempt
                    logger.warning(f"Got {r.status_code}; waiting {wait}s")
                    time.sleep(wait)
                else:
                    return r
            except requests.RequestException as e:
                logger.error(f"RequestException for {url}: {e}")
                time.sleep(1 + attempt)
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    def fetch_sitemaps(self):
        """Try several common sitemap locations and return article URLs found."""
        sitemap_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-posts.xml",
            "/sitemap1.xml",
            "/sitemap-index.xml"
        ]
        found = set()
        for sp in sitemap_paths:
            url = urljoin(self.base_url, sp)
            r = self.fetch(url)
            if not r or not r.text:
                continue
            text = r.text
            # quick check if it's XML-like
            if "<urlset" in text or "<sitemapindex" in text:
                logger.info(f"Parsing sitemap: {url}")
                try:
                    soup = BeautifulSoup(text, "xml")
                    for loc in soup.find_all("loc"):
                        loc_text = loc.get_text(strip=True)
                        if ARTICLE_RE.search(loc_text):
                            # normalize to base domain variant
                            parsed = urlparse(loc_text)
                            normalized = f"https://{parsed.netloc}{parsed.path}"
                            found.add(normalized)
                except Exception as e:
                    logger.error(f"Failed to parse sitemap {url}: {e}")
        logger.info(f"Sitemap discovered {len(found)} article URLs")
        return list(found)

    def debug_save(self, page_url, content):
        """Save HTML for manual inspection"""
        parsed = urlparse(page_url)
        name = parsed.path.strip("/").replace("/", "_") or "root"
        filename = f"{DEBUG_PREFIX}{name}.html"
        try:
            with open(filename, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")

    def get_links_from_page(self, page_url):
        """Fetch a page and extract article URLs using regex & anchors"""
        r = self.fetch(page_url)
        if not r or not r.text:
            return []
        html = r.text
        self.debug_save(page_url, html)

        soup = BeautifulSoup(html, "html.parser")
        links = set()

        # 1) Check anchor hrefs
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            # make absolute
            abs_href = urljoin(self.base_url, href)
            # match via regex
            m = ARTICLE_RE.search(href) or ARTICLE_RE.search(abs_href)
            if m:
                # normalize full absolute URL
                if abs_href.startswith("http"):
                    links.add(abs_href.split("?")[0].rstrip("/"))
                else:
                    full = urljoin(self.base_url, m.group(0))
                    links.add(full.split("?")[0].rstrip("/"))

        # 2) Also search raw HTML for article-like links (in scripts / JSON)
        for match in ARTICLE_RE.findall(html):
            if match.startswith("http"):
                links.add(match.split("?")[0].rstrip("/"))
            else:
                links.add(urljoin(self.base_url, match).split("?")[0].rstrip("/"))

        logger.info(f"Found {len(links)} article-like links on {page_url}")
        return sorted(links)

    def discover_article_urls(self, limit=200):
        """High-level discovery: sitemap -> listing pages -> fallback seeds"""
        # 1) Sitemap attempt
        urls = self.fetch_sitemaps()
        if urls:
            logger.info("Using sitemap-discovered URLs.")
            return urls[:limit]

        # 2) Try known listing pages (some may be JS-driven; we save debug HTML to inspect)
        start_pages = [
            f"{self.base_url}/t/",
            f"{self.base_url}/t/training",
            f"{self.base_url}/t/nutrition",
            f"{self.base_url}/t/supplements",
            f"{self.base_url}/training",
            f"{self.base_url}/nutrition",
        ]
        discovered = set()
        for p in start_pages:
            try:
                links = self.get_links_from_page(p)
                for l in links:
                    discovered.add(l)
                # polite pause
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error discovering from {p}: {e}")

        logger.info(f"Total discovered via pages: {len(discovered)}")
        if discovered:
            return sorted(discovered)[:limit]

        # 3) Fallback: check urls.txt (user-provided)
        txt_file = "urls.txt"
        if os.path.exists(txt_file):
            logger.info("Reading fallback URLs from urls.txt")
            with open(txt_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line: 
                        continue
                    if ARTICLE_RE.search(line):
                        discovered.add(line.split("?")[0].rstrip("/"))
            return sorted(discovered)[:limit]

        # none found
        return []

    def scrape_article(self, article_url):
        r = self.fetch(article_url)
        if not r or not r.text:
            return None
        soup = BeautifulSoup(r.text, "html.parser")

        # Title
        title_el = soup.select_one("h1") or soup.select_one(".topic-title") or soup.select_one(".article-title")
        title = title_el.get_text(strip=True) if title_el else None

        # date & author
        date_el = soup.select_one("time")
        date = date_el.get_text(strip=True) if date_el else None

        author_el = soup.select_one("a[rel='author']") or soup.select_one(".author") or soup.select_one(".byline")
        author = author_el.get_text(strip=True) if author_el else None

        # content: look for article tag, or common content containers
        content_selectors = ["article", ".topic-body", ".post", ".cooked", ".article__content", ".entry-content"]
        content_text = None
        for sel in content_selectors:
            node = soup.select_one(sel)
            if node:
                # remove scripts/styles
                for bad in node(["script", "style", "aside"]):
                    bad.decompose()
                # gather paragraphs
                paragraphs = [p.get_text(" ", strip=True) for p in node.find_all(["p", "h2", "h3"])]
                content_text = "\n\n".join([p for p in paragraphs if p])
                if content_text and len(content_text) > 80:
                    break

        if not title or not content_text:
            logger.warning(f"Article missing title or content: {article_url}")
            return None

        return {
            "url": article_url,
            "title": title,
            "author": author or "Unknown",
            "date_published": date or "Unknown",
            "content": content_text,
            "word_count": len(content_text.split()),
            "scraped_at": datetime.utcnow().isoformat() + "Z"
        }

    def run(self, limit=20, output_file=OUTPUT_FILE):
        logger.info("Starting discovery + scrape")
        urls = self.discover_article_urls(limit=limit)
        logger.info(f"Discovered {len(urls)} candidate article URLs")

        if len(urls) == 0:
            logger.error("No article URLs discovered. Check data/debug_*.html files to see what the fetch returned.")
            return []

        articles = []
        for i, u in enumerate(urls[:limit], 1):
            logger.info(f"Scraping ({i}/{min(limit,len(urls))}): {u}")
            art = self.scrape_article(u)
            if art:
                articles.append(art)
            time.sleep(1.5)

        # Save
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(articles, fh, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(articles)} articles to {output_file}")
        return articles


if __name__ == "__main__":
    scraper = TNationScraper()
    scraper.run(limit=10)


