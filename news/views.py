"""
Views for the news application.
Handles HTTP requests and delegates business logic to service modules.
"""
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View
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
from .sse_utils import sse_queue


class IndexView(APIView):
    """Render the main news feed page"""
    
    def get(self, request):
        return render(request, 'news_feed.html')


class CreateNewsView(View):
    """Render the news submission page"""
    
    def get(self, request):
        return render(request, 'create_news.html')


class CategorizedArticlesView(APIView):
    """Get all articles grouped by category"""
    
    def get(self, request):
        categorized_articles = CategorizationService.get_categorized_articles()
        return Response(categorized_articles)


class TrendAnalysisView(APIView):
    """Get trend analysis for all articles"""
    
    def get(self, request):
        trend_analysis = TrendAnalysisService.get_full_trend_analysis()
        return Response(trend_analysis)


class BucketsView(APIView):
    """Get all SimHash buckets"""
    
    def get(self, request):
        buckets = TendencyAnalysisService.get_buckets()
        return Response(buckets)


class SubmitNewsApiView(APIView):
    """Submit a new news article"""
    
    def post(self, request):
        try:
            # Create article in database
            article = ArticleService.create_article(request.data)
            
            # Convert to dictionary for processing
            article_dict = article.to_dict()
            
            # Add to tendency analyzer
            TendencyAnalysisService.add_article(article_dict)
            
            # Invalidate caches
            CacheService.invalidate_all()
            
            # Queue for SSE broadcast
            sse_queue.put(article_dict)
            
            return Response({
                "status": "success",
                "message": "Article submitted successfully.",
                "id": article.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SSEStreamView(View):
    """Server-Sent Events stream for real-time updates"""
    
    def get(self, request):
        response = StreamingHttpResponse(
            SSEStreamGenerator.generate(request),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable buffering for nginx
        return response
