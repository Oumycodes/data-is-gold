import requests
from bs4 import BeautifulSoup
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TNationScraper:
    def __init__(self):
        self.base_url = "https://www.t-nation.com"
        self.visited = set()
        self.output_file = os.path.join("data", "sample_output.json")

    def fetch_articles(self):
        url = f"{self.base_url}/training/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all article links (they usually start with /t/)
        links = [a["href"] for a in soup.find_all("a", href=True)]
        articles = [self.base_url + link for link in links if self.is_valid_article(link)]

        logger.info(f"Found {len(articles)} articles to scrape")
        return articles

    def is_valid_article(self, url):
        """Match URLs like /t/some-article-title/12345"""
        return url.startswith("/t/") and url not in self.visited

    def scrape_article(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Title is usually in <h1>
        title = soup.find("h1")
        title = title.get_text(strip=True) if title else "No Title"

        # Content is inside article tags
        paragraphs = soup.select("article p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])

        return {"url": url, "title": title, "content": content}

    def run(self):
        logger.info("Starting T-Nation scraper...")
        articles = self.fetch_articles()
        results = []

        for relative_url in articles:
            full_url = relative_url if relative_url.startswith("http") else self.base_url + relative_url
            if full_url in self.visited:
                continue
            self.visited.add(full_url)

            try:
                data = self.scrape_article(full_url)
                results.append(data)
                logger.info(f"Scraped: {data['title']}")
            except Exception as e:
                logger.error(f"Failed to scrape {full_url}: {e}")

        # Save results
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Scraping complete. Saved {len(results)} articles")


if __name__ == "__main__":
    scraper = TNationScraper()
    scraper.run()



