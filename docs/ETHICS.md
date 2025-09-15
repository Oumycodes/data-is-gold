
Interpretation:
- Public article pages (`/t/article-title/...`) are **not disallowed**, so scraping them does not violate robots.txt.
- Restricted paths are login pages, user data, and API keys — we will **not scrape these**.
- The sitemap provides a safe entry point for article discovery.

## Terms of Service Review
We reviewed T-Nation’s Terms of Service (as of Sept 2025). The ToS does not explicitly allow scraping, but it prohibits misuse of the website and unauthorized access to private accounts. Our scraping plan targets only **public, non-PII content (articles)** and complies with these guidelines.

## Ethical Framework
Our scraping strategy is designed to minimize harm and respect site operations:
- **Only scrape public articles** intended for public readership.
- **No PII**: we will not scrape user accounts, comments, or private data.
- **Polite scraping**: limit requests to ~1 every 2 seconds, with exponential backoff if errors occur.
- **Compliance**: respect `robots.txt`, ignore disallowed paths, and stop immediately if contacted by site administrators.
- **Data use**: scraped content will be used only for academic purposes (data structuring and proof-of-concept product), not for resale of raw content.

## Approval Request
We request instructor approval to proceed with scraping public T-Nation article pages for academic use in Project 2: Data is Gold.


