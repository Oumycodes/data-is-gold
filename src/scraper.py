import requests
from bs4 import BeautifulSoup
import logging
import json
import os
import re
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TNationScraper:
    def __init__(self):
        self.base_url = "https://www.t-nation.com"
        self.visited = set()
        self.articles = []

    def fetch(self, url):
        """Fetch HTML content from a URL safely"""
        try:
            logger.info(f"Fetching {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def safe_extract(self, soup, selectors):
        """Try multiple selectors until something is found"""
        for selector in selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def extract_content(self, soup):
        """Extract article body content"""
        content_selectors = [
            "article .article__content",
            "div.article-content",
            "section.main-content",
            "div.content",
            "article",
        ]
        for sel in content_selectors:
            section = soup.select_one(sel)
            if section:
                return section.get_text(" ", strip=True)
        return ""

    def scrape_article(self, url):
        """Scrape a single article"""
        html = self.fetch(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")

        title = self.safe_extract(soup, [
            "h1.article-title",
            "h1.entry-title",
            "h1",
            ".title",
            "title",
        ])
        author = self.safe_extract(soup, [
            ".author-name",
            ".byline",
            "meta[name='author']",
        ])
        date = self.safe_extract(soup, [
            "time",
            ".date",
            "meta[property='article:published_time']",
        ])
        content = self.extract_content(soup)

        return {
            "url": url,
            "title": title,
            "author": author,
            "date": date,
            "content": content,
        }

    def discover_articles(self, page_url):
        """Find article links on category pages"""
        html = self.fetch(page_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(self.base_url, href)
            if self.is_valid_article(full_url):
                links.append(full_url)
        return list(set(links))

    def is_valid_article(self, url):
        """Check if a URL looks like a real T-Nation article"""
        if not url.startswith(self.base_url):
            return False
        if url in self.visited:
            return False
        parsed = urlparse(url)
        return any(p in parsed.path for p in [
            "/training/",
            "/nutrition/",
            "/supplements/",
            "/workouts/",
            "/articles/",
            "/tips/",
            "/lean-built-eating/",
        ])

    def run_scraper(self, limit=5):
        """Main scrape loop"""
        logger.info("Starting T-Nation scraper...")

        article_pages_to_try = [
            f"{self.base_url}/training",
            f"{self.base_url}/nutrition",
            f"{self.base_url}/supplements",
            f"{self.base_url}/workouts",
        ]

        all_links = []
        for page in article_pages_to_try:
            all_links.extend(self.discover_articles(page))

        logger.info(f"Discovered {len(all_links)} candidate articles")

        for url in all_links[:limit]:  # scrape only a few for demo
            if url in self.visited:
                continue
            self.visited.add(url)
            article = self.scrape_article(url)
            if article and article["content"]:
                self.articles.append(article)
                logger.info(f"Scraped article: {article['title']}")

        # Save results
        os.makedirs("data", exist_ok=True)
        with open("data/tnation_articles.json", "w", encoding="utf-8") as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)

        logger.info(f"Scraping complete. Saved {len(self.articles)} articles.")


if __name__ == "__main__":
    scraper = TNationScraper()
    scraper.run_scraper(limit=5)

