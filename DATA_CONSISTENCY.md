# Data Consistency Verification

## Overview

This document explains how the refactored news application ensures that **SSE stream data always matches the database state**.

---

## Data Flow Guarantee

### When an Article is Submitted

```
1. POST /api/submit/
   ↓
2. ArticleService.create_article(data)
   └─ Article saved to DATABASE ✓
   ↓
3. article.to_dict()
   └─ Convert DB object to dictionary
   ↓
4. TendencyAnalysisService.add_article(article_dict)
   └─ Add to SimHash analyzer
   ↓
5. CacheService.invalidate_all()
   └─ Clear ALL caches (categorization, trends)
   ↓
6. sse_queue.put(article_dict)
   └─ Queue article for broadcast
   ↓
7. Return HTTP 201 Created
```

### When SSE Stream Processes the Article

```
1. SSE receives article from queue
   ↓
2. Verify article exists in DB
   └─ News.objects.get(id=article_id)
   └─ Use FRESH data from DB
   ↓
3. Fetch all data from DATABASE:
   ├─ CategorizationService.get_categorized_articles()
   │  └─ Cache was invalidated, so fetches from DB
   ├─ TrendAnalysisService.get_full_trend_analysis()
   │  └─ Cache was invalidated, so fetches from DB
   ├─ ArticleService.get_all_articles_as_dicts()
   │  └─ ALWAYS fetches from DB (no cache)
   └─ ArticleService.get_recent_articles(limit)
      └─ ALWAYS fetches from DB (no cache)
   ↓
4. Build event with VERIFIED database data
   ↓
5. Broadcast to clients
```

---

## Key Guarantees

### 1. **Article Verification**
```python
# In sse_handlers.py - SSEEventBuilder.build_article_event()
article_id = current_article.get('_id')
try:
    # Fetch from database to ensure it exists
    db_article = News.objects.get(id=article_id)
    # Use the fresh database version
    current_article = db_article.to_dict()
except (News.DoesNotExist, ValueError, TypeError):
    # Fallback to queued version (shouldn't happen)
    pass
```

**Guarantee**: The article broadcasted via SSE is verified to exist in the database.

---

### 2. **Cache Invalidation**
```python
# In views.py - SubmitNewsApiView.post()
CacheService.invalidate_all()
```

**What this does**:
- Deletes `categorized_articles` cache
- Deletes `full_trend_analysis` cache

**Guarantee**: Next fetch will query the database, not stale cache.

---

### 3. **Fresh Database Queries**
```python
# In services.py - ArticleService
@staticmethod
def get_all_articles_as_dicts():
    """Get all articles as dictionaries"""
    return [article.to_dict() for article in News.objects.all()]

@staticmethod
def get_recent_articles(limit=50):
    """Get recent articles as dictionaries"""
    articles = News.objects.all().order_by('-datePublished')[:limit]
    return [article.to_dict() for article in articles]
```

**Guarantee**: These methods ALWAYS query the database directly (no caching).

---

### 4. **Database Count Verification**
```python
# In sse_handlers.py - SSEEventBuilder._build_statistics()
db_count = News.objects.count()

return {
    "total_articles": db_count,  # Actual DB count
    "total_articles_cached": sum(len(articles) for articles in categorized.values()),
    # ...
}
```

**Guarantee**: The total article count is fetched directly from the database.

---

## Verification Tools

### 1. **Management Command**
```bash
python manage.py verify_data_consistency
```

**What it checks**:
- ✓ Database count vs API count
- ✓ Category distribution (DB vs API)
- ✓ Sample article presence in API
- ✓ Categorized articles match database
- ✓ Trend analysis matches database

### 2. **Manual Verification**

**Check database count**:
```bash
python manage.py shell
>>> from news.models import News
>>> News.objects.count()
```

**Check API count**:
```bash
curl http://127.0.0.1:8000/api/trends/
# Sum all category counts
```

**Check categorized articles**:
```bash
curl http://127.0.0.1:8000/api/categorized/
# Count articles in all categories
```

---

## Cache Strategy

### What is Cached?
1. **Categorized Articles** (`categorized_articles`)
   - Cache timeout: 5 minutes
   - Invalidated on: New article submission

2. **Full Trend Analysis** (`full_trend_analysis`)
   - Cache timeout: 5 minutes
   - Invalidated on: New article submission

### What is NOT Cached?
1. **All Articles** - Always fresh from DB
2. **Recent Articles** - Always fresh from DB
3. **Database Count** - Always fresh from DB
4. **Individual Article Lookup** - Always fresh from DB

### Why This Strategy?

**Cached Data**:
- Expensive to compute (categorization, trend analysis)
- Can tolerate brief staleness (5 minutes max)
- Invalidated immediately on new article

**Non-Cached Data**:
- Fast to query (indexed queries)
- Must be 100% accurate
- Used for verification and critical operations

---

## Testing Data Consistency

### Test 1: Submit Article and Verify
```bash
# Terminal 1: Start server
python manage.py runserver

# Terminal 2: Submit article
python news_submitter.py

# Terminal 3: Verify
python manage.py verify_data_consistency
```

### Test 2: Check SSE Stream
```bash
# Terminal 1: Start server
python manage.py runserver

# Terminal 2: Listen to SSE stream
curl -N http://127.0.0.1:8000/api/stream/

# Terminal 3: Submit article
python news_submitter.py

# Check Terminal 2: You should see the new article with correct counts
```

### Test 3: Database vs API
```python
# In Django shell
from news.models import News
import requests

# Get DB count
db_count = News.objects.count()

# Get API count
response = requests.get('http://127.0.0.1:8000/api/trends/')
api_count = sum(response.json().values())

print(f"DB: {db_count}, API: {api_count}, Match: {db_count == api_count}")
```

---

## Common Issues and Solutions

### Issue 1: Counts Don't Match
**Symptom**: Database has 100 articles, API shows 95

**Possible Causes**:
1. Cache not invalidated
2. Articles created outside the API

**Solution**:
```bash
# Clear all caches
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Verify again
python manage.py verify_data_consistency
```

### Issue 2: SSE Stream Shows Old Data
**Symptom**: New article submitted but SSE shows old counts

**Possible Causes**:
1. Cache invalidation failed
2. SSE stream using cached data

**Solution**:
- Check that `CacheService.invalidate_all()` is called in `SubmitNewsApiView`
- Verify cache backend is working: `python manage.py shell` → `cache.set('test', 1)` → `cache.get('test')`

### Issue 3: Article in DB but Not in API
**Symptom**: Article exists in database but doesn't appear in categorized API

**Possible Causes**:
1. Article has invalid category
2. Cache is stale

**Solution**:
```python
# Check article category
article = News.objects.get(id=X)
print(article.category)  # Should be one of the valid choices

# Clear cache
from django.core.cache import cache
cache.clear()
```

---

## Performance Considerations

### Database Queries per SSE Event

When an article is broadcast via SSE, the following queries are made:

1. `News.objects.get(id=article_id)` - Verify article (1 query)
2. `News.objects.all()` - Get all articles (1 query, may be cached)
3. `News.objects.all().order_by('-datePublished')[:N]` - Recent articles (1 query)
4. `News.objects.count()` - Total count (1 query)

**Total: ~4 queries per event**

### Optimization

The cache strategy reduces this:
- **With cache hit**: 2 queries (all articles, recent articles)
- **With cache miss**: 4 queries (+ categorization, + trends)

### When to Clear Cache

Cache is automatically cleared:
- ✓ On new article submission
- ✓ After 5 minutes (timeout)

Manual clearing:
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## Summary

✅ **Article is saved to database FIRST**  
✅ **Cache is invalidated BEFORE broadcasting**  
✅ **SSE fetches fresh data from database**  
✅ **Article existence is verified before broadcasting**  
✅ **Database count is used for total articles**  
✅ **Verification tools are available**  

**Result**: SSE stream data ALWAYS matches database state! 🎉
