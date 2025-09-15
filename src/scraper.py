import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
from urllib.parse import urljoin

class TNationForumScraper:
    def __init__(self):
        self.base_url = "https://forums.t-nation.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tnation_forum_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        os.makedirs("data", exist_ok=True)

    def fetch_page(self, url):
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code == 200:
                return r.text
            else:
                self.logger.warning(f"Bad status {r.status_code} for {url}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def get_topic_links(self, category_slug="training"):
        """Scrape links to forum topics from a category page"""
        url = f"{self.base_url}/c/{category_slug}/36"  # training category
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a in soup.select("a.title"):
            href = a.get("href")
            if href and href.startswith("/t/"):
                full = urljoin(self.base_url, href)
                links.append(full)

        self.logger.info(f"Found {len(links)} topics in category {category_slug}")
        return list(set(links))  # deduplicate

    def scrape_topic(self, url):
        """Scrape a single topic page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Extract posts (all text from .cooked divs)
        posts = []
        for div in soup.select("div.cooked"):
            text = div.get_text(" ", strip=True)
            if text:
                posts.append(text)

        if not posts:
            self.logger.warning(f"No posts found in {url}")
            return None

        return {
            "url": url,
            "title": title,
            "post_count": len(posts),
            "content": posts,
            "scraped_at": datetime.now().isoformat()
        }

    def run(self, categories=["training", "nutrition"], limit=10, output_file="data/tnation_forum.json"):
        all_data = []
        for cat in categories:
            topic_links = self.get_topic_links(cat)
            self.logger.info(f"Scraping {min(limit, len(topic_links))} topics from {cat}...")

            for link in topic_links[:limit]:
                data = self.scrape_topic(link)
                if data:
                    all_data.append(data)
                time.sleep(1)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Saved {len(all_data)} topics to {output_file}")
        return all_data


if __name__ == "__main__":
    scraper = TN



