import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
from urllib.parse import urljoin, urlparse

class TNationScraper:
    def __init__(self):
        self.base_url = "https://t-nation.com"
        self.session = requests.Session()
        
        # Enhanced headers to avoid bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        
        self.retry_delays = [1, 2, 4, 8]  # Exponential backoff
        
        # Setup enhanced logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tnation_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
    
    def scrape_with_backoff(self, url, max_retries=4):
        """Implement exponential backoff for respectful scraping"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Requesting: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=15)
                
                self.logger.info(f"Response status: {response.status_code} for {url}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        delay = self.retry_delays[attempt]
                        self.logger.warning(f"Rate limited. Waiting {delay}s...")
                        time.sleep(delay)
                        continue
                elif response.status_code == 403:
                    self.logger.warning(f"Access forbidden (403) for {url}")
                    if attempt < max_retries - 1:
                        time.sleep(self.retry_delays[attempt])
                        continue
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Request failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                    continue
        
        self.logger.error(f"Failed to retrieve {url} after {max_retries} attempts")
        return None
    
    def debug_homepage(self):
        """Debug what's actually on the homepage"""
        response = self.scrape_with_backoff(self.base_url)
        if not response:
            self.logger.error("Could not access homepage for debugging")
            return
        
        # Save homepage HTML for inspection
        with open('debug_homepage.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        self.logger.info("Homepage HTML saved to debug_homepage.html")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Show page title
        title = soup.find('title')
        self.logger.info(f"Homepage title: {title.text if title else 'No title found'}")
        
        # Debug: Count all links
        all_links = soup.find_all('a', href=True)
        self.logger.info(f"Found {len(all_links)} total links on homepage")
        
        # Debug: Show sample of links
        self.logger.info("Sample of links found:")
        for i, link in enumerate(all_links[:20]):  # Show first 20 links
            href = link.get('href')
            text = link.get_text().strip()[:50]  # First 50 chars
            self.logger.info(f"  {i+1}: {href} -> {text}")
    
    def get_article_links(self):
        """Get article links from T-Nation with enhanced discovery"""
        self.logger.info("Starting article discovery...")
        
        # First, debug the homepage
        self.debug_homepage()
        
        # Try multiple discovery strategies
        article_links = set()
        
        # Strategy 1: Homepage
        homepage_links = self._get_links_from_page(self.base_url)
        article_links.update(homepage_links)
        self.logger.info(f"Found {len(homepage_links)} links from homepage")
        
        # Strategy 2: Try common article listing pages
        article_pages_to_try = [
            f"{self.base_url}/all-articles",
            f"{self.base_url}/training",
            f"{self.base_url}/nutrition", 
            f"{self.base_url}/supplements",
            f"{self.base_url}/articles"
        ]
        
        for page_url in article_pages_to_try:
            self.logger.info(f"Trying article listing page: {page_url}")
            page_links = self._get_links_from_page(page_url)
            if page_links:
                article_links.update(page_links)
                self.logger.info(f"Found {len(page_links)} additional links from {page_url}")
            time.sleep(1)  # Be respectful
        
        final_links = list(article_links)
        self.logger.info(f"Total unique article links discovered: {len(final_links)}")
        
        # Debug: Show discovered links
        if final_links:
            self.logger.info("Sample of discovered article URLs:")
            for i, link in enumerate(final_links[:10]):
                self.logger.info(f"  {i+1}: {link}")
        else:
            self.logger.error("No article links found! Check selectors and URL patterns.")
        
        return final_links[:20]  # Limit for testing
    
    def _get_links_from_page(self, page_url):
        """Extract article links from a single page"""
        response = self.scrape_with_backoff(page_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        # Enhanced URL patterns - look for more patterns
        url_patterns = [
            '/training/',
            '/nutrition/', 
            '/supplements/',
            '/workouts/',
            '/lean-built-eating/',
            '/article/',
            '/tip/',
            '/blog/',
            '/post/'
        ]
        
        # Get all links
        article_links = soup.find_all('a', href=True)
        self.logger.info(f"Found {len(article_links)} total links on {page_url}")
        
        for link in article_links:
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                
                # Check if this looks like an article
                if self._is_likely_article_url(href, url_patterns):
                    if full_url not in links:
                        links.append(full_url)
                        self.logger.debug(f"Added article URL: {full_url}")
        
        return links
    
    def _is_likely_article_url(self, href, patterns):
        """Check if URL looks like an article"""
        if not href:
            return False
            
        href_lower = href.lower()
        
        # Skip obvious non-article URLs
        skip_patterns = [
            '/search', '/login', '/register', '/category', '/tag', 
            '/author', '/page/', '#', 'javascript:', 'mailto:', 'tel:',
            '/contact', '/about', '/privacy', '/terms'
        ]
        
        if any(skip in href_lower for skip in skip_patterns):
            return False
        
        # Check for article patterns
        if any(pattern in href_lower for pattern in patterns):
            return True
        
        # Also accept URLs with meaningful paths (not just navigation)
        if href.count('/') >= 2 and len(href) > 10:
            # Additional check: avoid admin/system paths
            admin_patterns = ['/wp-', '/admin', '/api', '/feed', '/rss']
            if not any(admin in href_lower for admin in admin_patterns):
                return True
        
        return False
    
    def scrape_article(self, article_url):
        """Scrape individual article content with enhanced extraction"""
        self.logger.info(f"Scraping article: {article_url}")
        
        response = self.scrape_with_backoff(article_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article data with multiple fallbacks
        title = self.safe_extract(soup, [
            'h1', 
            '.entry-title', 
            '.post-title',
            '.article-title',
            '.title',
            'title'
        ])
        
        content = self.extract_content(soup)
        
        # Enhanced validation
        if not title:
            self.logger.warning(f"No title found for {article_url}")
            return None
        
        if not content or len(content) < 100:
            self.logger.warning(f"No content or content too short for {article_url} (length: {len(content) if content else 0})")
            return None
        
        # Extract additional metadata
        author = self.safe_extract(soup, [
            '.author',
            '.byline', 
            '[class*="author"]',
            '[itemprop="author"]'
        ])
        
        date_published = self.safe_extract(soup, [
            'time',
            '.date',
            '.published',
            '[class*="date"]',
            '[itemprop="datePublished"]'
        ])
        
        article_data = {
            'url': article_url,
            'title': title,
            'author': author or 'Unknown',
            'date_published': date_published or 'Unknown',
            'content': content,
            'word_count': len(content.split()),
            'reading_time': max(1, len(content.split()) // 200),
            'scraped_at': datetime.now().isoformat()
        }
        
        self.logger.info(f"Successfully scraped: {title[:50]}... ({article_data['word_count']} words)")
        return article_data
    
    def safe_extract(self, soup, selectors):
        """Safely extract text from multiple selector options"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:  # Make sure we got actual text
                        return text
            except Exception as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        return None
    
    def extract_content(self, soup):
        """Extract main article content with multiple strategies"""
        content_selectors = [
            'article', 
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content', 
            'main',
            '[class*="content"]'
        ]
        
        for selector in content_selectors:
            try:
                content_div = soup.select_one(selector)
                if content_div:
                    # Remove script and style elements
                    for script in content_div(["script", "style"]):
                        script.decompose()
                    
                    text = content_div.get_text(strip=True)
                    if text and len(text) > 100:  # Must have substantial content
                        return text
            except Exception as e:
                self.logger.debug(f"Content selector '{selector}' failed: {e}")
                continue
        
        return None
    
    def run_scraper(self, output_file='data/tnation_articles.json'):
        """Main scraper execution with enhanced error handling"""
        self.logger.info("Starting T-Nation scraper...")
        
        # Test basic connectivity first
        test_response = self.scrape_with_backoff(self.base_url)
        if not test_response:
            self.logger.error("Cannot connect to T-Nation. Check internet connection or try VPN.")
            return []
        
        # Get article links
        article_links = self.get_article_links()
        
        if not article_links:
            self.logger.error("No article links found. Scraper needs debugging.")
            return []
        
        self.logger.info(f"Found {len(article_links)} articles to scrape")
        
        articles = []
        successful_scrapes = 0
        
        for i, link in enumerate(article_links):
            self.logger.info(f"Processing article {i+1}/{len(article_links)}")
            
            article = self.scrape_article(link)
            if article:
                articles.append(article)
                successful_scrapes += 1
                
                # Save progress every 5 articles
                if successful_scrapes % 5 == 0:
                    try:
                        progress_file = f"data/tnation_articles_progress_{successful_scrapes}.json"
                        with open(progress_file, 'w', encoding='utf-8') as f:
                            json.dump(articles, f, indent=2, ensure_ascii=False)
                        self.logger.info(f"Progress saved: {successful_scrapes} articles")
                    except Exception as e:
                        self.logger.error(f"Failed to save progress: {e}")
                
            # Respectful delay between requests
            time.sleep(2)
        
        # Save final results
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Final results saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save final data: {e}")
        
        self.logger.info(f"Scraping complete. Successfully scraped {len(articles)} out of {len(article_links)} articles")
        
        if len(articles) == 0:
            self.logger.error("No articles were scraped! Check the debug files and logs.")
        
        return articles

if __name__ == "__main__":
    scraper = TNationScraper()
    scraper.run_scraper()
