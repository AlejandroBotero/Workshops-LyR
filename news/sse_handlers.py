"""
Server-Sent Events (SSE) handlers for real-time news updates.
"""
import json
import time
import queue

from .models import News
from .services import (
    ArticleService,
    CategorizationService,
    TrendAnalysisService,
    RelatedArticleService,
    TendencyAnalysisService,
)
from .sse_utils import sse_queue
from .hasher import compare_news_objects
from .markov_service import MarkovChainService


class SSEEventBuilder:
    """Builds SSE event data payloads"""
    
    @staticmethod
    def build_article_event(current_article, last_n=50):
        """
        Build a complete event payload for a new article.
        Ensures all data is fetched fresh from the database.
        
        Args:
            current_article: The new article dictionary
            last_n: Number of recent articles to analyze
            
        Returns:
            dict: Complete event data with database-verified information
        """
        # Verify the article exists in the database and get fresh data
        article_id = current_article.get('_id')
        try:
            # Fetch the article from database to ensure it exists
            db_article = News.objects.get(id=article_id)
            # Use the fresh database version
            current_article = db_article.to_dict()
        except (News.DoesNotExist, ValueError, TypeError):
            # If article not found in DB, use the queued version
            # This shouldn't happen in normal flow but handles edge cases
            pass
        
        # Get categorized articles and trends (fresh from DB after cache invalidation)
        categorized_articles = CategorizationService.get_categorized_articles()
        full_trend_analysis = TrendAnalysisService.get_full_trend_analysis()
        
        # Get all articles and recent articles (always fresh from DB)
        # all_articles = ArticleService.get_all_articles_as_dicts() # REMOVED for performance
        recent_articles = ArticleService.get_recent_articles(limit=last_n)
        
        # Analyze recent trends
        recent_trend_analysis = TrendAnalysisService.analyze_trends(recent_articles)
        
        # Get top tendencies
        top_tendencies = TendencyAnalysisService.get_top_tendencies()
        
        # Get Markov chain graph data
        markov_graph = MarkovChainService.get_markov_graph_data()
        
        # Find related article
        related_article = RelatedArticleService.find_related_article(
            current_article
        )
        
        # Calculate similarity distance if related article found
        related_similarity_distance = "N/A"
        if related_article is not None:
            related_similarity_distance = compare_news_objects(
                current_article, 
                related_article
            )
        
        # Build statistics
        statistics = SSEEventBuilder._build_statistics(
            categorized_articles,
            full_trend_analysis,
            recent_trend_analysis,
            top_tendencies,
            last_n
        )
        
        return {
            "new_article": current_article,
            "related_article": related_article,
            "related_similarity_distance": related_similarity_distance,
            "statistics": statistics,
            "markov_graph": markov_graph,
        }
    
    @staticmethod
    def _build_statistics(categorized, full_trends, recent_trends, top_tendencies, last_n):
        """Build statistics section of event data"""
        # Verify total count matches database
        db_count = News.objects.count()
        
        return {
            "total_articles": db_count,  # Use actual DB count
            "total_articles_cached": sum(len(articles) for articles in categorized.values()),
            "category_counts": {
                category: len(articles) 
                for category, articles in categorized.items()
            },
            "full_trend_analysis": full_trends,
            "recent_trend_analysis": recent_trends,
            "last_n": last_n,
            "top_tendencies": top_tendencies,
        }


class SSEStreamGenerator:
    """Generates SSE stream for real-time updates"""
    
    HEARTBEAT_TIMEOUT = 10  # seconds
    SLEEP_INTERVAL = 1  # seconds
    
    @staticmethod
    def generate(request):
        """
        Generate SSE event stream.
        Ensures all data sent matches what's in the database.
        
        Args:
            request: HTTP request object
            
        Yields:
            str: SSE formatted events
        """
        last_n = SSEStreamGenerator._parse_last_n(request)
        
        # Send initial data (latest article) if available
        try:
            latest_article = News.objects.first()
            if latest_article:
                event_data = SSEEventBuilder.build_article_event(latest_article.to_dict(), last_n)
                yield f"data: {json.dumps(event_data)}\n\n"
        except Exception as e:
            # Log error but continue to stream loop
            print(f"Error sending initial data: {e}")

        while True:
            try:
                # Wait for new article from queue
                current_article = sse_queue.get(timeout=SSEStreamGenerator.HEARTBEAT_TIMEOUT)
                
                # Build event data (this fetches fresh data from DB)
                event_data = SSEEventBuilder.build_article_event(current_article, last_n)
                
                # Yield SSE formatted data
                yield f"data: {json.dumps(event_data)}\n\n"
                
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield ":heartbeat\n\n"
            except Exception as e:
                # Log error but keep stream alive
                error_data = {
                    "error": "Failed to build event",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            
            time.sleep(SSEStreamGenerator.SLEEP_INTERVAL)
    
    @staticmethod
    def _parse_last_n(request):
        """Parse last_n parameter from request"""
        last_n_str = request.GET.get('last_n', '50')
        try:
            return int(last_n_str)
        except ValueError:
            return 50  # Default value
