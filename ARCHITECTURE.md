# Architecture Overview

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     HTTP Request Layer                       │
│                        (views.py)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  IndexView   │  │ Categorized  │  │ TrendAnalysis│      │
│  │              │  │ ArticlesView │  │    View      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ SubmitNews   │  │ SSEStreamView│                        │
│  │   ApiView    │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│                      (services.py)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Article    │  │Categorization│  │TrendAnalysis │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │RelatedArticle│  │  Tendency    │  │    Cache     │      │
│  │   Service    │  │   Analysis   │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SSE Streaming Layer                       │
│                    (sse_handlers.py)                         │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │SSEEventBuilder│  │SSEStreamGen  │                        │
│  │              │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Models    │  │    Utils     │  │    Hasher    │      │
│  │  (models.py) │  │  (utils.py)  │  │ (hasher.py)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow

### Example: Submitting a News Article

```
1. HTTP POST /api/submit/
   ↓
2. SubmitNewsApiView.post()
   ↓
3. ArticleService.create_article(data)
   ├─ Parse date
   ├─ Create News object in DB
   └─ Return article instance
   ↓
4. TendencyAnalysisService.add_article(article_dict)
   └─ Add to SimHash analyzer
   ↓
5. CacheService.invalidate_all()
   ├─ Clear categorization cache
   └─ Clear trend analysis cache
   ↓
6. sse_queue.put(article_dict)
   └─ Queue for real-time broadcast
   ↓
7. Return HTTP 201 Response
```

### Example: SSE Stream

```
1. HTTP GET /api/stream/
   ↓
2. SSEStreamView.get()
   ↓
3. SSEStreamGenerator.generate(request)
   ├─ Parse last_n parameter
   └─ Enter event loop
       ↓
4. Wait for article from queue
   ↓
5. SSEEventBuilder.build_article_event()
   ├─ CategorizationService.get_categorized_articles()
   ├─ TrendAnalysisService.get_full_trend_analysis()
   ├─ ArticleService.get_all_articles_as_dicts()
   ├─ ArticleService.get_recent_articles(last_n)
   ├─ TrendAnalysisService.analyze_trends()
   ├─ TendencyAnalysisService.get_top_tendencies()
   └─ RelatedArticleService.find_related_article()
   ↓
6. Format as SSE event
   ↓
7. Yield to client
   ↓
8. Repeat (or send heartbeat if timeout)
```

## Service Dependencies

```
ArticleService
  └─ News (model)

CategorizationService
  ├─ ArticleCategorizer (utils)
  └─ Django Cache

TrendAnalysisService
  ├─ News (model)
  └─ Django Cache

RelatedArticleService
  └─ compare_news_objects (hasher)

TendencyAnalysisService
  └─ SimHashTendencyAnalyzer (utils)

CacheService
  ├─ CategorizationService
  └─ TrendAnalysisService
```

## File Responsibilities

| File | Lines | Responsibility | Dependencies |
|------|-------|----------------|--------------|
| `views.py` | 86 | HTTP handling | services, sse_handlers |
| `services.py` | 225 | Business logic | models, utils, hasher |
| `sse_handlers.py` | 120 | SSE streaming | services, hasher |
| `models.py` | 62 | Data models | Django ORM |
| `utils.py` | 121 | Utilities | models, hasher |
| `hasher.py` | 80 | SimHash logic | - |

## Key Improvements

### 1. Separation of Concerns
- **Views**: Only HTTP request/response
- **Services**: Only business logic
- **SSE Handlers**: Only streaming logic

### 2. Single Responsibility
Each service class has one clear purpose:
- `ArticleService` → Article CRUD
- `CategorizationService` → Categorization
- `TrendAnalysisService` → Trend analysis
- `RelatedArticleService` → Finding related articles
- `TendencyAnalysisService` → SimHash tendencies
- `CacheService` → Cache management

### 3. Testability
```python
# Easy to test in isolation
def test_create_article():
    data = {'headline': 'Test'}
    article = ArticleService.create_article(data)
    assert article.headline == 'Test'

# Easy to mock
@patch('news.services.News.objects')
def test_with_mock(mock_objects):
    # Test without database
```

### 4. Reusability
Services can be used anywhere:
- Views
- Management commands
- Background tasks
- API endpoints
- Admin actions

### 5. Maintainability
- Clear file organization
- Easy to locate code
- Changes are isolated
- Self-documenting structure
