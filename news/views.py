from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import ArticleCategorizer
from .hasher import simhash_news_object, compare_news_objects # Import simhash_news_object, compare_news_objects
from .sse_utils import sse_queue
from .utils import SimHashTendencyAnalyzer # Import SimHashTendencyAnalyzer
import json
import time
import queue
import os
import threading # Import threading for lock

import random # new import needed

NEWS_DATA_PATH = 'news_data.json'

# Global SimHash Tendency Analyzer
simhash_tendency_analyzer_instance = SimHashTendencyAnalyzer(similarity_threshold=15) # Use a similarity threshold

# Define the similarity threshold for related articles
RELATED_ARTICLE_SIMILARITY_THRESHOLD = 15 # Example value, can be adjusted


def get_related_article(current_article, all_articles):
    current_category = current_article.get('category')
    if not current_category:
        return None

    candidate_articles_in_category = [
        article for article in all_articles
        if article.get('category') == current_category and article.get('_id') != current_article.get('_id')
    ]

    filtered_related_articles = []
    for candidate_article in candidate_articles_in_category:
        similarity_distance = compare_news_objects(current_article, candidate_article)
        if similarity_distance is not None and similarity_distance < RELATED_ARTICLE_SIMILARITY_THRESHOLD:
            filtered_related_articles.append(candidate_article)

    if filtered_related_articles:
        return random.choice(filtered_related_articles)
    return None

def get_categorized_articles():
    categorized_articles = cache.get('categorized_articles')
    if not categorized_articles:
        categorizer = ArticleCategorizer(NEWS_DATA_PATH)
        categorized_articles = categorizer.categorize_articles()
        cache.set('categorized_articles', categorized_articles)
    return categorized_articles

def get_trend_analysis(news_articles):
    category_counts = {}
    for article in news_articles:
        category = article.get('category', 'unknown')
        category_counts[category] = category_counts.get(category, 0) + 1
    return category_counts

def get_full_trend_analysis():
    full_trend_analysis = cache.get('full_trend_analysis')
    if not full_trend_analysis:
        if os.path.exists(NEWS_DATA_PATH):
            with open(NEWS_DATA_PATH, 'r') as file:
                news_data = json.load(file)
            
            category_counts = {}
            for article in news_data:
                category = article.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            full_trend_analysis = category_counts
            cache.set('full_trend_analysis', full_trend_analysis)
        else:
            full_trend_analysis = {} # Return empty if no data file
    return full_trend_analysis

class IndexView(APIView):
    def get(self, request):
        return render(request, 'news_feed.html')

class CategorizedArticlesView(APIView):
    def get(self, request):
        categorized_articles = get_categorized_articles()
        return Response(categorized_articles)

class TrendAnalysisView(APIView):
    def get(self, request):
        full_trend_analysis = get_full_trend_analysis()
        return Response(full_trend_analysis)

class SubmitNewsApiView(APIView):
    def post(self, request):
        new_article = request.data
        
        # Add article to SimHash Tendency Analyzer
        simhash_tendency_analyzer_instance.add_article(new_article)

        with open(NEWS_DATA_PATH, 'r+') as file:
            news_data = json.load(file)
            news_data.append(new_article)
            file.seek(0)
            json.dump(news_data, file, indent=4)

        # Invalidate the cache
        cache.delete('categorized_articles')
        cache.delete('full_trend_analysis')

        # Send the new article to the SSE queue
        sse_queue.put(new_article)

        return Response({"status": "success", "message": "Article submitted successfully."})

def _event_stream_generator(request):
    while True:
        try:
            current_article = sse_queue.get(timeout=10) # Wait for a new article
            
            # Recalculate categorized articles and full trend analysis
            categorized_articles = get_categorized_articles()
            full_trend_analysis = get_full_trend_analysis()

            # Load all news data for recent trends
            news_data = []
            if os.path.exists(NEWS_DATA_PATH):
                with open(NEWS_DATA_PATH, 'r') as file:
                    news_data = json.load(file)

            # Get 'last_n' from request, default to 50
            last_n_str = request.GET.get('last_n', '50')
            try:
                last_n = int(last_n_str)
            except ValueError:
                last_n = 50 # Default if not a valid number
            
            recent_articles = news_data[-last_n:] if len(news_data) > last_n else news_data

            recent_trend_analysis = get_trend_analysis(recent_articles)
            
            
            # Get top tendencies from SimHash Tendency Analyzer
            top_tendencies = simhash_tendency_analyzer_instance.get_top_tendencies()

            # Find a related article
            related_article = get_related_article(current_article, news_data)
            
            related_similarity_distance = "N/A"
            if related_article is not None:
                related_similarity_distance = compare_news_objects(current_article, related_article)


            data = {
                "new_article": current_article,
                "related_article": related_article, # Pass the related article
                "related_similarity_distance": related_similarity_distance, # Pass the Hamming distance
                "statistics": {
                    "total_articles": sum(len(articles) for articles in categorized_articles.values()),
                    "category_counts": {category: len(articles) for category, articles in categorized_articles.items()},
                    "full_trend_analysis": full_trend_analysis,
                    "recent_trend_analysis": recent_trend_analysis,
                    "last_n": last_n, # Include last_n in the data
                    "top_tendencies": top_tendencies, # Include top tendencies
                }
            }
            
            yield f"data: {json.dumps(data)}\n\n"
        except queue.Empty:
            # Send a heartbeat to keep the connection alive
            yield ":heartbeat\n\n"
        time.sleep(1)

class SSEStreamView(View):
    def get(self, request):
        response = StreamingHttpResponse(_event_stream_generator(request), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response
