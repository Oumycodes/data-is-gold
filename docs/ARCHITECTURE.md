## Scraping Complexity Matrix – T-Nation

| Feature               | Difficulty (1–5) | Strategy                                                                 |
|------------------------|------------------|--------------------------------------------------------------------------|
| Dynamic JS content     | 2                | Main article content is static (in raw HTML). Some interactive parts (likes, comments) may load via JS. Use `requests + BeautifulSoup` for static HTML, and check Network tab for XHR endpoints if dynamic data is needed. |
| Rate limiting          | 3                | No obvious strict limits in light testing, but Discourse-based forums often throttle heavy usage. Use polite scraping: 1 request every 2s, exponential backoff on failures, retry limit, and stop on repeated errors. |
| Data structure varies  | 2                | Most articles follow a consistent template. Some pages may have missing fields (e.g., no images). Write validators in `validators.py` to ensure required fields (title, date, body) are present, and transformers to normalize formats. |
| Session management     | 1                | Public pages do not require login. Use simple `requests.Session()` for persistence of headers/cookies if needed. |


