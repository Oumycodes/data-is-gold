import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import logging

class TNationScraper:
    def __init__(self):
        self.base_url = "https://t-nation.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.retry_delays = [1, 2, 4, 8]  # Exponential backoff
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def scrape_with_backoff(self, url, max_retries=4):
        """Implement exponential backoff for respectful scraping"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        delay = self.retry_delays[attempt]
                        self.logger.info(f"Rate limited. Waiting {delay}s...")
                        time.sleep(delay)
                        continue
            except requests.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                    continue
        return None
    
    def get_article_links(self):
        """Get article links from T-Nation homepage"""
        response = self.scrape_with_backoff(self.base_url)
        
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        # Look for article links - adjust selectors based on actual site
        article_links = soup.find_all('a', href=True)
        for link in article_links:
            href = link.get('href')
            if href and ('/training/' in href or '/workouts/' in href or '/lean-built-eating/' in href):
                full_url = self.base_url + href if href.startswith('/') else href
                if full_url not in links:
                    links.append(full_url)
        
        return links[:5]  # Limit to 5 for demo
    
    def scrape_article(self, article_url):
        """Scrape individual article content"""
        response = self.scrape_with_backoff(article_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article data - simplified selectors
        title = self.safe_extract(soup, ['h1', '.title', 'title'])
        content = self.extract_content(soup)
        
        if not title or not content or len(content) < 100:
            return None
        
        article_data = {
            'url': article_url,
            'title': title,
            'content': content,
            'word_count': len(content.split()),
            'reading_time': max(1, len(content.split()) // 200),
            'scraped_at': datetime.now().isoformat()
        }
        
        return article_data
    
    def safe_extract(self, soup, selectors):
        """Safely extract text from multiple selector options"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None
    
    def extract_content(self, soup):
        """Extract main article content"""
        content_selectors = [
            'article', 
            '.content', 
            '.article-content',
            '.post-content',
            'main'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                return content_div.get_text(strip=True)
        
        return None
    
    def run_scraper(self, output_file='data/tnation_articles.json'):
        """Main scraper execution"""
        self.logger.info("Starting T-Nation scraper...")
        
        # Get article links
        article_links = self.get_article_links()
        self.logger.info(f"Found {len(article_links)} articles to scrape")
        
        articles = []
        for i, link in enumerate(article_links):
            self.logger.info(f"Scraping article {i+1}/{len(article_links)}: {link}")
            
            article = self.scrape_article(link)
            if article:
                articles.append(article)
                
            # Respectful delay between requests
            time.sleep(1)
        
        # Save results
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
        
        self.logger.info(f"Scraping complete. Saved {len(articles)} articles")
        return articles

if __name__ == "__main__":
    scraper = TNationScraper()
    scraper.run_scraper()
