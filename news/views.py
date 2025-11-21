from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import ArticleCategorizer, TrendAnalyzer
from .sse_utils import sse_queue
from .bloom_filter import BloomFilter # Import Bloom Filter
from .minwise_sampler import MinWiseSampler # Import MinWiseSampler
from .flajolet_martin import FlajoletMartin # Import FlajoletMartin
from .ams_moment import AMSMomentEstimator # Import AMSMomentEstimator
import json
import time
import queue
import os
import threading # Import threading for lock

NEWS_DATA_PATH = 'news_data.json'

# Global Bloom Filter and counters
bloom_filter_instance = BloomFilter(capacity=10000, error_rate=0.01)
total_articles_processed = 0
unique_articles_added = 0
redundant_articles_caught = 0
bloom_filter_lock = threading.Lock() # Lock for thread-safe access to Bloom Filter and counters

# Global MinWise Sampler
minwise_sampler_instance = MinWiseSampler(sample_size=3) # Sample 3 articles per category

# Global Flajolet-Martin estimator
flajolet_martin_instance = FlajoletMartin(num_bits=32, num_hash_functions=5) # 5 estimators for better accuracy

# Global AMS Moment Estimator
ams_estimator_instance = AMSMomentEstimator(num_estimators=10) # 10 estimators for better accuracy


def get_categorized_articles():
    categorized_articles = cache.get('categorized_articles')
    if not categorized_articles:
        categorizer = ArticleCategorizer(NEWS_DATA_PATH)
        categorized_articles = categorizer.categorize_articles()
        cache.set('categorized_articles', categorized_articles)
    return categorized_articles

def get_trend_analysis(news_articles):
    trend_analyzer = TrendAnalyzer(width=1000, depth=5)
    for article in news_articles:
        category = article.get('category', 'unknown') # Use original category
        popularity_score = article.get('popularity_score', 1) # Default to 1 if score is missing
        trend_analyzer.add(category, weight=popularity_score)

    categories_in_articles = set(article.get('category', 'unknown') for article in news_articles)
    trend_analysis = {}
    for category in categories_in_articles:
        estimate = trend_analyzer.estimate(category)
        trend_analysis[category] = estimate
    return trend_analysis

def get_full_trend_analysis():
    full_trend_analysis = cache.get('full_trend_analysis')
    if not full_trend_analysis:
        if os.path.exists(NEWS_DATA_PATH):
            with open(NEWS_DATA_PATH, 'r') as file:
                news_data = json.load(file)
            full_trend_analysis = get_trend_analysis(news_data)
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
        global total_articles_processed, unique_articles_added, redundant_articles_caught
        new_article = request.data
        
        # Prepare article identifier for Bloom Filter
        article_identifier = f"{new_article.get('headline', '')}-{new_article.get('content', '')}"
        
        category = new_article.get('category', 'unknown') # Use original category for AMS

        with bloom_filter_lock: # Acquire lock for thread-safe access
            total_articles_processed += 1
            if article_identifier in bloom_filter_instance:
                redundant_articles_caught += 1
            else:
                bloom_filter_instance.add(article_identifier)
                unique_articles_added += 1
                flajolet_martin_instance.add(article_identifier) # Add to FM if unique
                ams_estimator_instance.add(category) # Add category to AMS

        with open(NEWS_DATA_PATH, 'r+') as file:
            news_data = json.load(file)
            news_data.append(new_article)
            file.seek(0)
            json.dump(news_data, file, indent=4)

        # Add article to MinWise Sampler
        minwise_sampler_instance.add_article(new_article, category)

        # Invalidate the cache
        cache.delete('categorized_articles')
        cache.delete('full_trend_analysis')

        # Send the new article to the SSE queue
        sse_queue.put(new_article)

        return Response({"status": "success", "message": "Article submitted successfully."})

def _event_stream_generator(request):
    while True:
        try:
            article = sse_queue.get(timeout=10) # Wait for a new article
            
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

            data = {
                "new_article": article,
                "statistics": {
                    "total_articles": sum(len(articles) for articles in categorized_articles.values()),
                    "category_counts": {category: len(articles) for category, articles in categorized_articles.items()},
                    "full_trend_analysis": full_trend_analysis,
                    "recent_trend_analysis": recent_trend_analysis,
                    "last_n": last_n, # Include last_n in the data
                    "bloom_filter": bf_stats, # Include Bloom Filter statistics
                    "minwise_samples": minwise_samples, # Include MinWise Samples
                    "flajolet_martin_estimate": flajolet_martin_instance.estimate_distinct_count(), # Include FM estimate
                    "ams_second_moment_estimate": ams_estimator_instance.estimate_second_moment(), # Include AMS estimate
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
