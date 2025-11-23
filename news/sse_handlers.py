"""
Server-Sent Events (SSE) handlers for real‑time news updates.
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
from .hasher import compare_news_objects
from .markov_service import MarkovChainService
from .sse_utils import sse_channel


class SSEEventBuilder:
    """Builds the payload for an SSE event.

    All data is freshly fetched from the database to guarantee consistency.
    """

    @staticmethod
    def build_article_event(current_article, last_n=50):
        """Create a complete event payload for a new article.

        Args:
            current_article (dict): The article dict (may be stale).
            last_n (int): Number of recent articles to analyse.
        """
        # Ensure we have the latest version from the DB
        article_id = current_article.get('_id')
        try:
            db_article = News.objects.get(id=article_id)
            current_article = db_article.to_dict()
        except (News.DoesNotExist, ValueError, TypeError):
            pass

        categorized_articles = CategorizationService.get_categorized_articles()
        full_trend_analysis = TrendAnalysisService.get_full_trend_analysis()
        recent_articles = ArticleService.get_recent_articles(limit=last_n)
        recent_trend_analysis = TrendAnalysisService.analyze_trends(recent_articles)
        top_tendencies = TendencyAnalysisService.get_top_tendencies()
        markov_graph = MarkovChainService.get_markov_graph_data()
        related_article = RelatedArticleService.find_related_article(current_article)
        related_similarity_distance = "N/A"
        if related_article is not None:
            related_similarity_distance = compare_news_objects(current_article, related_article)

        statistics = SSEEventBuilder._build_statistics(
            categorized_articles,
            full_trend_analysis,
            recent_trend_analysis,
            top_tendencies,
            last_n,
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
        """Collect statistics for the event payload."""
        db_count = News.objects.count()
        return {
            "total_articles": db_count,
            "total_articles_cached": sum(len(arts) for arts in categorized.values()),
            "category_counts": {cat: len(arts) for cat, arts in categorized.items()},
            "full_trend_analysis": full_trends,
            "recent_trend_analysis": recent_trends,
            "last_n": last_n,
            "top_tendencies": top_tendencies,
        }


class SSEStreamGenerator:
    """Generates an SSE stream for real‑time updates."""

    HEARTBEAT_TIMEOUT = 10  # seconds
    SLEEP_INTERVAL = 1  # seconds

    @staticmethod
    def generate(request):
        """Yield SSE‑formatted events.

        The generator first sends an initial payload (or a placeholder if the DB is empty),
        then subscribes the client to the global ``sse_channel`` and streams new articles.
        """
        last_n = SSEStreamGenerator._parse_last_n(request)

        # ---- Initial payload -------------------------------------------------
        try:
            latest_article = News.objects.order_by('-datePublished').first()
            if latest_article:
                event_data = SSEEventBuilder.build_article_event(latest_article.to_dict(), last_n)
                yield f"data: {json.dumps(event_data)}\n\n"
            else:
                # No articles yet – send a friendly placeholder
                yield f"data: {json.dumps({'message': 'No articles yet'})}\n\n"
        except Exception as e:
            # Log the problem and still keep the stream alive
            print(f"Error sending initial data: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        # ---- Subscribe the client -------------------------------------------
        client_queue = sse_channel.listen()
        try:
            while True:
                try:
                    # Wait for a new article (or timeout for heartbeat)
                    current_article = client_queue.get(timeout=SSEStreamGenerator.HEARTBEAT_TIMEOUT)
                    event_data = SSEEventBuilder.build_article_event(current_article, last_n)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except queue.Empty:
                    # Heartbeat keeps the connection alive for proxies/load‑balancers
                    yield ":heartbeat\n\n"
                except Exception as e:
                    print(f"Error in stream loop: {e}")
                    import traceback
                    traceback.print_exc()
                    error_payload = {"error": "Failed to build event", "message": str(e)}
                    yield f"data: {json.dumps(error_payload)}\n\n"
                time.sleep(SSEStreamGenerator.SLEEP_INTERVAL)
        except GeneratorExit:
            # Normal client disconnect (e.g., browser navigation)
            print("Client disconnected (GeneratorExit)")
        except Exception as e:
            print(f"Unexpected stream error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sse_channel.unlisten(client_queue)
            print("Client disconnected, listener removed.")

    @staticmethod
    def _parse_last_n(request):
        """Extract ``last_n`` query param, defaulting to 50."""
        try:
            return int(request.GET.get('last_n', '50'))
        except ValueError:
            return 50
