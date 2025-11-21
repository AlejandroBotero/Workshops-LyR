import json
import hashlib
import re # Added for SimHash tokenization
from collections import defaultdict # Added for SimHashTendencyAnalyzer
import random # Added for random sample headline selection
from news.hasher import simhash_news_object, get_hamming_distance # Import necessary SimHash functions

class ArticleCategorizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.categories = {}

    def load_data(self):
        # Ensure the data file exists and is not empty
        try:
            with open(self.data_path, 'r') as file:
                content = file.read()
                if content:
                    return json.loads(content)
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def categorize_articles(self):
        articles = self.load_data()
        self.categories = {} # Reset categories for each categorization run
        for article in articles:
            # Use the original category from the article
            category = article.get('category')
            
            if category: # Only categorize if a category is present
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(article)
        return self.categories



class SimHashTendencyAnalyzer:
    def __init__(self, similarity_threshold=3): # Hamming distance threshold for similarity
        self.similarity_threshold = similarity_threshold
        # Stores buckets. Each bucket is a list of articles.
        # Key: representative_simhash, Value: list of articles in that bucket
        self.buckets = defaultdict(list)
        # Store simhashes of all articles to quickly check for existing buckets
        # This will store {article_simhash: [article1, article2, ...]}
        # For simplicity in this implementation, we'll directly use self.buckets
        # with representative_simhash. The simhash_to_articles might be redundant for basic bucketing.

    def add_article(self, article):
        """
        Adds an article to the appropriate SimHash bucket.
        """
        article_simhash = simhash_news_object(article)
        
        # Try to find an existing bucket for this article
        found_bucket = False
        # Create a list of current keys to avoid "dictionary changed size during iteration" error
        for representative_simhash in list(self.buckets.keys()): 
            distance = get_hamming_distance(article_simhash, representative_simhash)
            if distance <= self.similarity_threshold:
                self.buckets[representative_simhash].append(article)
                found_bucket = True
                break
        
        if not found_bucket:
            # If no suitable bucket found, create a new one with this article's simhash as representative
            self.buckets[article_simhash].append(article)

    def get_top_tendencies(self, num_tendencies=3):
        """
        Identifies and returns the top N tendencies (topics) based on bucket size.
        A tendency is represented by its most frequent category and a sample headline.
        Returns a list of dictionaries, e.g., [{"topic": "Technology", "count": 10, "sample_headline": "..."}].
        """
        # Sort buckets by size (number of articles) in descending order
        sorted_buckets = sorted(self.buckets.items(), key=lambda item: len(item[1]), reverse=True)
        
        top_tendencies = []
        for representative_simhash, articles_in_bucket in sorted_buckets:
            if not articles_in_bucket:
                continue

            # Determine the most frequent category in the bucket
            category_counts = defaultdict(int)
            for article in articles_in_bucket:
                category_counts[article.get('category', 'unknown')] += 1
            
            most_frequent_category = max(category_counts, key=category_counts.get) if category_counts else "General News"
            
            # Get a sample headline from an article belonging to the most frequent category
            sample_headline = 'No Headline'
            
            # Collect all articles from the most frequent category within this bucket
            articles_of_most_frequent_category = [
                article for article in articles_in_bucket 
                if article.get('category') == most_frequent_category
            ]

            if articles_of_most_frequent_category:
                # Pick a random article's headline from this subset
                sample_article = random.choice(articles_of_most_frequent_category)
                sample_headline = sample_article.get('headline', 'No Headline')
            
            top_tendencies.append({
                "topic": most_frequent_category,
                "count": len(articles_in_bucket),
                "sample_headline": sample_headline
            })
            
            if len(top_tendencies) >= num_tendencies:
                break
                
        return top_tendencies

