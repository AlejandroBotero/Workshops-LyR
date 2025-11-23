"""
Business logic services for news articles.
Handles article operations, categorization, trend analysis, and related article discovery.
"""
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
import random

from django.db.models import Count
from .models import News
from .utils import ArticleCategorizer, SimHashTendencyAnalyzer
from .hasher import compare_news_objects


# Constants
RELATED_ARTICLE_SIMILARITY_THRESHOLD = 15
CACHE_TIMEOUT = 300  # 5 minutes

# Global SimHash Tendency Analyzer instance
simhash_tendency_analyzer = SimHashTendencyAnalyzer(similarity_threshold=15)


class ArticleService:
    """Service for managing news articles"""
    
    @staticmethod
    def create_article(data):
        """
        Create a new news article from submitted data.
        
        Args:
            data: Dictionary containing article data
            
        Returns:
            News: Created News instance
        """
        date_published = ArticleService._parse_date(data.get('datePublished'))
        
        article = News.objects.create(
            headline=data.get('headline', ''),
            content=data.get('content', ''),
            category=data.get('category', 'world'),
            datePublished=date_published,
            popularity_score=data.get('popularity_score', 0),
            engagementLevel=data.get('engagementLevel', 'low'),
        )
        
        return article
    
    @staticmethod
    def _parse_date(date_value):
        """Parse date from various formats"""
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except ValueError:
                return timezone.now()
        elif date_value is None:
            return timezone.now()
        return date_value
    
    @staticmethod
    def get_all_articles_as_dicts():
        """Get all articles as dictionaries"""
        return [article.to_dict() for article in News.objects.all()]
    
    @staticmethod
    def get_recent_articles(limit=50):
        """Get recent articles as dictionaries"""
        articles = News.objects.all().order_by('-datePublished')[:limit]
        return [article.to_dict() for article in articles]


class CategorizationService:
    """Service for article categorization"""
    
    @staticmethod
    def get_categorized_articles():
        """
        Get categorized articles with caching.
        
        Returns:
            dict: Articles grouped by category
        """
        cache_key = 'categorized_articles'
        categorized = cache.get(cache_key)
        
        if not categorized:
            categorizer = ArticleCategorizer()
            categorized = categorizer.categorize_articles()
            cache.set(cache_key, categorized, CACHE_TIMEOUT)
        
        return categorized
    
    @staticmethod
    def invalidate_cache():
        """Invalidate categorization cache"""
        cache.delete('categorized_articles')


class TrendAnalysisService:
    """Service for trend analysis"""
    
    @staticmethod
    def analyze_trends(articles):
        """
        Analyze trends from a list of article dictionaries.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            dict: Category counts
        """
        category_counts = {}
        for article in articles:
            category = article.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
    
    @staticmethod
    def get_full_trend_analysis():
        """
        Get full trend analysis with caching.
        
        Returns:
            dict: Category counts for all articles
        """
        cache_key = 'full_trend_analysis'
        analysis = cache.get(cache_key)
        
        if not analysis:
        if not analysis:
            # Use DB aggregation for performance
            category_counts = dict(
                News.objects.values_list('category').annotate(count=Count('category'))
            )
            
            analysis = category_counts
            cache.set(cache_key, analysis, CACHE_TIMEOUT)
        
        return analysis
    
    @staticmethod
    def invalidate_cache():
        """Invalidate trend analysis cache"""
        cache.delete('full_trend_analysis')


class RelatedArticleService:
    """Service for finding related articles"""
    
    @staticmethod
    def find_related_article(current_article, limit=50, threshold=RELATED_ARTICLE_SIMILARITY_THRESHOLD):
        """
        Find a related article based on category and similarity.
        Searches only recent articles in the same category for performance.
        
        Args:
            current_article: Current article dictionary
            limit: Max number of recent articles to check
            threshold: Similarity threshold (Hamming distance)
            
        Returns:
            dict or None: Related article if found
        """
        current_category = current_article.get('category')
        if not current_category:
            return None
        
        # Fetch only recent articles in the same category from DB
        # Exclude the current article itself
        candidates_qs = News.objects.filter(category=current_category).exclude(
            id=current_article.get('_id')
        ).order_by('-datePublished')[:limit]
        
        candidates = [article.to_dict() for article in candidates_qs]
        
        # Find similar articles
        similar_articles = []
        for candidate in candidates:
            similarity_distance = compare_news_objects(current_article, candidate)
            if similarity_distance is not None and similarity_distance < threshold:
                similar_articles.append(candidate)
        
        # Return random similar article if any found
        return random.choice(similar_articles) if similar_articles else None


class TendencyAnalysisService:
    """Service for SimHash tendency analysis"""
    
    _initialized = False

    @classmethod
    def _ensure_initialized(cls):
        """Ensure the analyzer is populated from the database"""
        # Check if database is empty (e.g. after reset)
        if News.objects.count() == 0:
            if simhash_tendency_analyzer.buckets:
                simhash_tendency_analyzer.buckets.clear()
            cls._initialized = True
            return

        if not cls._initialized:
            # Check if buckets are empty to avoid double loading if initialized elsewhere
            if not simhash_tendency_analyzer.buckets:
                # Use iterator to avoid loading all objects into memory at once
                # Only fetch fields needed for to_dict (or just what's needed for SimHash if optimized)
                # SimHash needs: headline, content, category
                all_articles = News.objects.all().iterator()
                for article in all_articles:
                    simhash_tendency_analyzer.add_article(article.to_dict())
            cls._initialized = True

    @staticmethod
    def add_article(article_dict):
        """Add article to tendency analyzer"""
        TendencyAnalysisService._ensure_initialized()
        simhash_tendency_analyzer.add_article(article_dict)
    
    @staticmethod
    def get_top_tendencies(num_tendencies=5):
        """Get top trending topics"""
        TendencyAnalysisService._ensure_initialized()
        return simhash_tendency_analyzer.get_top_tendencies(num_tendencies)

    @staticmethod
    def get_buckets():
        """Get all SimHash buckets"""
        TendencyAnalysisService._ensure_initialized()
        
        # Convert to serializable format
        buckets_data = {}
        for simhash_key, articles in simhash_tendency_analyzer.buckets.items():
            buckets_data[str(simhash_key)] = articles
        return buckets_data


class CacheService:
    """Service for cache management"""
    
    @staticmethod
    def invalidate_all():
        """Invalidate all news-related caches"""
        CategorizationService.invalidate_cache()
        TrendAnalysisService.invalidate_cache()
