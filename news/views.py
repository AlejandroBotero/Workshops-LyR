from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import ArticleCategorizer, TrendAnalyzer
from .sse_utils import sse_queue
import json
import time
import queue

def get_categorized_articles():
    categorized_articles = cache.get('categorized_articles')
    if not categorized_articles:
        categorizer = ArticleCategorizer('news_data.json')
        categorized_articles = categorizer.categorize_articles()
        cache.set('categorized_articles', categorized_articles)
    return categorized_articles

def get_trend_analysis():
    trend_analysis = cache.get('trend_analysis')
    if not trend_analysis:
        trend_analyzer = TrendAnalyzer(width=1000, depth=5)
        with open('news_data.json', 'r') as file:
            news_data = json.load(file)
        
        for article in news_data:
            trend_analyzer.add(article['category'])

        categories = set(article['category'] for article in news_data)
        trend_analysis = {}
        for category in categories:
            estimate = trend_analyzer.estimate(category)
            trend_analysis[category] = estimate
        cache.set('trend_analysis', trend_analysis)
    return trend_analysis

class IndexView(APIView):
    def get(self, request):
        return render(request, 'news_feed.html')

class CategorizedArticlesView(APIView):
    def get(self, request):
        categorized_articles = get_categorized_articles()
        return Response(categorized_articles)

class TrendAnalysisView(APIView):
    def get(self, request):
        trend_analysis = get_trend_analysis()
        return Response(trend_analysis)

class SubmitNewsApiView(APIView):
    def post(self, request):
        new_article = request.data
        
        with open('news_data.json', 'r+') as file:
            news_data = json.load(file)
            news_data.append(new_article)
            file.seek(0)
            json.dump(news_data, file, indent=4)

        # Invalidate the cache
        cache.delete('categorized_articles')
        cache.delete('trend_analysis')

        # Send the new article to the SSE queue
        sse_queue.put(new_article)

        return Response({"status": "success", "message": "Article submitted successfully."})

def event_stream():
    while True:
        try:
            article = sse_queue.get(timeout=10)
            categorized_articles = get_categorized_articles()
            trend_analysis = get_trend_analysis()
            
            data = {
                "new_article": article,
                "statistics": {
                    "total_articles": sum(len(articles) for articles in categorized_articles.values()),
                    "category_counts": {category: len(articles) for category, articles in categorized_articles.items()},
                    "trend_analysis": trend_analysis
                }
            }
            
            yield f"data: {json.dumps(data)}\n\n"
        except queue.Empty:
            # Send a heartbeat to keep the connection alive
            yield ":heartbeat\n\n"
        time.sleep(1)

class SSEStreamView(View):
    def get(self, request):
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response
