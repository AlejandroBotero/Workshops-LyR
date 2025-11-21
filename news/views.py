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

NEWS_DATA_PATH = 'news_data.json'

# Global SimHash Tendency Analyzer
simhash_tendency_analyzer_instance = SimHashTendencyAnalyzer(similarity_threshold=3) # Use a similarity threshold

# Global variable to store the hash of the last article for similarity comparison
last_full_article = None


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
        print("\n\ngotten new article: \n", new_article)
        
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
    global last_full_article # Declare global to modify it
    while True:
        try:
            current_article = sse_queue.get(timeout=10) # Wait for a new article
            
            similarity_distance = "N/A"
            if last_full_article is not None:
                similarity_distance = compare_news_objects(last_full_article, current_article)
            
            # Store the current article as the last one for the next iteration
            last_news = last_full_article # Renaming for clarity to frontend
            last_full_article = current_article
            
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
            
            with bloom_filter_lock: # Acquire lock for thread-safe access to counters
                bf_stats = {
                    "total_processed": total_articles_processed,
                    "unique_added": unique_articles_added,
                    "redundant_caught": redundant_articles_caught,
                    "bloom_filter_count": bloom_filter_instance.count,
                    "bit_array": list(bloom_filter_instance.bit_array), # Include the bit array
                    "capacity": bloom_filter_instance.capacity,
                    "error_rate": bloom_filter_instance.error_rate,
                    "num_bits": bloom_filter_instance.num_bits,
                    "num_hashes": bloom_filter_instance.num_hashes,
                }
            
            minwise_samples = minwise_sampler_instance.get_all_samples()
            
            # Get top tendencies from SimHash Tendency Analyzer
            top_tendencies = simhash_tendency_analyzer_instance.get_top_tendencies()

            data = {
                "new_article": current_article,
                "last_news": last_news, # Pass the previous full article
                "similarity": similarity_distance, # Pass the Hamming distance
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
