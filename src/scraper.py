import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
from urllib.parse import urljoin

class TNationScraper:
    def __init__(self):
        self.base_url = "https://www.t-nation.com"
        self.session = requests.Session()
        
        # Headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.retry_delays = [1, 2, 4, 8]
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tnation_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        os.makedirs('data', exist_ok=True)

    def scrape_with_backoff(self, url, max_retries=4):
        """Request with retries and backoff"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    return response
                elif response.status_code in [403, 429]:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays)-1)]
                    self.logger.warning(f"{response.status_code} error. Waiting {delay}s...")
                    time.sleep(delay)
            except requests.RequestException as e:
                self.logger.error(f"Request failed {url}: {e}")
                time.sleep(self.retry_delays[min(attempt, len(self.retry_delays)-1)])
        return None

    def get_article_links(self):
        """Discover article links from T-Nation"""
        self.logger.info("Starting article discovery...")

        article_links = set()

        start_pages = [
            f"{self.base_url}/t/",
            f"{self.base_url}/t/training",
            f"{self.base_url}/t/nutrition",
            f"{self.base_url}/t/supplements",
        ]

        for page_url in start_pages:
            self.logger.info(f"Checking page: {page_url}")
            page_links = self._get_links_from_page(page_url)
            article_links.update(page_links)
            time.sleep(1)

        final_links = list(article_links)
        self.logger.info(f"Total unique article links discovered: {len(final_links)}")

        for i, link in enumerate(final_links[:10]):
            self.logger.info(f"Sample {i+1}: {link}")

        return final_links[:20]

    def _get_links_from_page(self, page_url):
        """Extract links that look like articles"""
        response = self.scrape_with_backoff(page_url)
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("/t/"):
                # Skip non-article pages
                if any(skip in href for skip in ["/t/tag/", "/t/categories/", "/t/authors/"]):
                    continue
                full_url = urljoin(self.base_url, href)
                links.append(full_url)

        self.logger.info(f"Found {len(links)} article-like links on {page_url}")
        return links

    def scrape_article(self, article_url):
        """Scrape article details"""
        self.logger.info(f"Scraping: {article_url}")
        response = self.scrape_with_backoff(article_url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title = self.safe


