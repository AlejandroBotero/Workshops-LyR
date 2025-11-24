# Views for the news application.
# Handles HTTP requests and delegates business logic to service modules.

import os
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import (
    ArticleService,
    CategorizationService,
    TrendAnalysisService,
    TendencyAnalysisService,
    CacheService,
)
from .sse_handlers import SSEStreamGenerator
from .sse_utils import sse_channel

# ---------------------------------------------------------------------------
# Home page (news feed) – cached for 5 minutes in development
# ---------------------------------------------------------------------------
@method_decorator(cache_page(300), name='dispatch')
class IndexView(APIView):
    """Render the main news feed page.

    The template receives ``base_url`` so that it can build the correct
    EventSource URL both locally (http://127.0.0.1:8000) and on Azure.
    """

    def get(self, request):
        base_url = os.getenv('BASE_URL', 'http://127.0.0.1:8000')
        return render(request, 'news_feed.html', {'base_url': base_url})


# ---------------------------------------------------------------------------
# Simple page for submitting a new article
# ---------------------------------------------------------------------------
class CreateNewsView(View):
    """Render the news submission page."""

    def get(self, request):
        return render(request, 'create_news.html')


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
class CategorizedArticlesView(APIView):
    """Get all articles grouped by category."""

    def get(self, request):
        categorized_articles = CategorizationService.get_categorized_articles()
        return Response(categorized_articles)


class TrendAnalysisView(APIView):
    """Get trend analysis for all articles."""

    def get(self, request):
        trend_analysis = TrendAnalysisService.get_full_trend_analysis()
        return Response(trend_analysis)


class BucketsView(APIView):
    """Get all SimHash buckets."""

    def get(self, request):
        buckets = TendencyAnalysisService.get_buckets()
        return Response(buckets)


@method_decorator(csrf_exempt, name='dispatch')
class SubmitNewsApiView(APIView):
    """Submit a new news article via POST."""

    def post(self, request):
        try:
            # Persist the article
            article = ArticleService.create_article(request.data)
            article_dict = article.to_dict()

            # Update tendency analysis and clear caches
            TendencyAnalysisService.add_article(article_dict)
            CacheService.invalidate_all()

            # Broadcast to SSE listeners
            sse_channel.publish(article_dict)

            return Response(
                {
                    "status": "success",
                    "message": "Article submitted successfully.",
                    "id": article.id,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------------------------------------------------------------------
# SSE stream endpoint
# ---------------------------------------------------------------------------
class SSEStreamView(View):
    """Server‑Sent Events stream for real‑time updates."""

    def get(self, request):
        response = StreamingHttpResponse(
            SSEStreamGenerator.generate(request),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable buffering for nginx
        return response
