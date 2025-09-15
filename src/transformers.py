import re
import csv
import json
from datetime import datetime
from collections import Counter

class ContentTransformer:
    """Transform and enrich scraped content"""
    
    def __init__(self):
        self.exercise_patterns = [
            'squat', 'deadlift', 'bench press', 'pull-up', 'push-up', 
            'row', 'press', 'curl', 'lunge', 'plank'
        ]
        
        self.muscle_groups = [
            'chest', 'back', 'shoulders', 'biceps', 'triceps', 
            'legs', 'quads', 'hamstrings', 'glutes', 'calves',
            'abs', 'core'
        ]
    
    def transform_article(self, article_data):
        """Add value-added fields to article"""
        if not article_data:
            return None
            
        transformed = article_data.copy()
        
        # Clean content
        transformed['content'] = self.clean_content(transformed.get('content', ''))
        
        # Add enrichment fields
        transformed['exercises_mentioned'] = self.extract_exercises(transformed['content'])
        transformed['muscle_groups'] = self.extract_muscle_groups(transformed['content'])
        transformed['workout_type'] = self.classify_workout_type(transformed['content'])
        transformed['difficulty_level'] = self.estimate_difficulty(transformed['content'])
        
        return transformed
    
    def clean_content(self, content):
        """Clean and normalize content text"""
        if not content:
            return ""
            
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        content = re.sub(r'(Advertisement|Click here|Read more)', '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def extract_exercises(self, text):
        """Extract exercise names from content"""
        if not text:
            return []
            
        text_lower = text.lower()
        exercises_found = []
        
        for exercise in self.exercise_patterns:
            if exercise in text_lower:
                exercises_found.append(exercise)
        
        return list(set(exercises_found))  # Remove duplicates
    
    def extract_muscle_groups(self, text):
        """Extract mentioned muscle groups"""
        if not text:
            return []
            
        text_lower = text.lower()
        muscles_found = []
        
        for muscle in self.muscle_groups:
            if muscle in text_lower:
                muscles_found.append(muscle)
        
        return muscles_found
    
    def classify_workout_type(self, text):
        """Classify the type of workout based on content"""
        if not text:
            return 'general'
            
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['strength', 'powerlifting', 'heavy']):
            return 'strength'
        elif any(word in text_lower for word in ['muscle', 'size', 'bodybuilding']):
            return 'hypertrophy'  
        elif any(word in text_lower for word in ['cardio', 'endurance', 'running']):
            return 'endurance'
        elif any(word in text_lower for word in ['hiit', 'interval', 'circuit']):
            return 'hiit'
        else:
            return 'general'
    
    def estimate_difficulty(self, text):
        """Estimate workout difficulty level"""
        if not text:
            return 'beginner'
            
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['advanced', 'expert', 'brutal', 'intense']):
            return 'advanced'
        elif any(word in text_lower for word in ['intermediate', 'moderate']):
            return 'intermediate'
        else:
            return 'beginner'

class DataExporter:
    """Export transformed data in various formats"""
    
    def to_csv(self, articles, filename='data/tnation_articles.csv'):
        """Export articles to CSV format"""
        if not articles:
            print("No articles to export")
            return
            
        fieldnames = articles[0].keys()
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for article in articles:
                    # Handle lists by converting to strings
                    row = {}
                    for key, value in article.items():
                        if isinstance(value, list):
                            row[key] = ', '.join(map(str, value))
                        else:
                            row[key] = value
                    writer.writerow(row)
            print(f"Exported {len(articles)} articles to {filename}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
    
    def create_summary_report(self, articles, filename='data/summary_report.txt'):
        """Generate summary report of scraped data"""
        if not articles:
            print("No articles for summary")
            return
            
        total_articles = len(articles)
        total_words = sum(article.get('word_count', 0) for article in articles)
        
        # Most common workout types
        workout_types = [article.get('workout_type', 'unknown') for article in articles]
        workout_counter = Counter(workout_types)
        
        report = f"""T-Nation Scraping Summary Report
================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dataset Overview:
- Total Articles: {total_articles}
- Total Words: {total_words:,}
- Average Words per Article: {total_words // total_articles if total_articles > 0 else 0}

Top Workout Types:
"""
        
        for workout_type, count in workout_counter.most_common(5):
            report += f"  {workout_type}: {count}\n"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Summary report saved to {filename}")
        except Exception as e:
            print(f"Error creating summary: {e}")
