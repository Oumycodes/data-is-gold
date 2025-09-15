import re
from datetime import datetime

class ArticleValidator:
    """Validate scraped article data quality"""
    
    def __init__(self):
        self.min_content_length = 100
        self.required_fields = ['title', 'content', 'url']
        self.fitness_keywords = [
            'workout', 'exercise', 'training', 'muscle', 'strength', 
            'fitness', 'bodybuilding', 'lifting', 'gym', 'rep',
            'sets', 'weight', 'protein', 'diet', 'nutrition'
        ]
    
    def is_valid_article(self, article_data):
        """Main validation method"""
        if not self.has_required_fields(article_data):
            return False
            
        if not self.has_sufficient_content(article_data):
            return False
            
        if not self.is_fitness_related(article_data):
            return False
            
        return True
    
    def has_required_fields(self, article_data):
        """Check if article has all required fields"""
        for field in self.required_fields:
            if not article_data.get(field) or not str(article_data[field]).strip():
                return False
        return True
    
    def has_sufficient_content(self, article_data):
        """Check if article has enough content"""
        content = article_data.get('content', '')
        return len(content) >= self.min_content_length
    
    def is_fitness_related(self, article_data):
        """Check if article is fitness-related using keywords"""
        text = f"{article_data.get('title', '')} {article_data.get('content', '')}".lower()
        
        # Check if any fitness keywords are present
        for keyword in self.fitness_keywords:
            if keyword in text:
                return True
        return False
    
    def validate_url(self, url):
        """Validate URL format"""
        if not url:
            return False
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None

class DataQualityChecker:
    """Simple data quality metrics"""
    
    def __init__(self):
        self.validator = ArticleValidator()
        self.total_articles = 0
        self.valid_articles = 0
    
    def check_article_quality(self, articles):
        """Check quality of scraped articles"""
        if not articles:
            return "No articles to check"
        
        self.total_articles = len(articles)
        self.valid_articles = 0
        
        for article in articles:
            if self.validator.is_valid_article(article):
                self.valid_articles += 1
        
        return self.get_quality_report()
    
    def get_quality_report(self):
        """Generate simple quality report"""
        if self.total_articles == 0:
            return "No articles processed"
            
        valid_rate = (self.valid_articles / self.total_articles) * 100
        
        report = f"""
Data Quality Report:
===================
Total Articles: {self.total_articles}
Valid Articles: {self.valid_articles}
Quality Rate: {valid_rate:.1f}%
Invalid Articles: {self.total_articles - self.valid_articles}
"""
        return report
