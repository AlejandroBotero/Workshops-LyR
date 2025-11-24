# Async/SSE Production Setup Guide

## Overview
This document explains the asynchronous setup for Server-Sent Events (SSE) in production using Gunicorn with gevent workers.

## Dependencies Added

### 1. **gevent** (Primary Async Worker)
- **Purpose**: Provides greenlet-based concurrency for Python
- **Why needed**: Gunicorn's default sync workers block on long-running connections like SSE streams
- **What it does**: Enables thousands of concurrent SSE connections without blocking

### 2. **greenlet** (Coroutine Support)
- **Purpose**: Lightweight concurrent programming primitive
- **Why needed**: Required by gevent for cooperative multitasking
- **What it does**: Allows context switching between multiple SSE streams efficiently

## Gunicorn Configuration

### Updated startup.sh
```bash
gunicorn --bind=0.0.0.0:8000 \
  --workers=3 \
  --worker-class=gevent \
  --timeout 600 \
  --graceful-timeout 30 \
  news_api.wsgi
```

### Configuration Explained

1. **`--workers=3`**
   - Runs 3 worker processes
   - Each worker can handle thousands of concurrent connections
   - Formula: (2 × CPU cores) + 1 is recommended

2. **`--worker-class=gevent`**
   - **CRITICAL for SSE**: Uses gevent async workers instead of sync workers
   - Enables non-blocking I/O for long-lived SSE connections
   - Without this, each SSE connection blocks an entire worker

3. **`--timeout 600`**
   - Worker timeout set to 600 seconds (10 minutes)
   - Prevents workers from being killed during long SSE streams
   - Should be longer than your longest expected SSE connection

4. **`--graceful-timeout 30`**
   - Gives workers 30 seconds to finish requests during shutdown
   - Allows SSE streams to close gracefully
   - Prevents abrupt connection drops during deployment

## How It Works

### Without gevent (Sync Workers)
```
Worker 1: [SSE Client 1] ← BLOCKED, can't handle more requests
Worker 2: [SSE Client 2] ← BLOCKED, can't handle more requests
Worker 3: [SSE Client 3] ← BLOCKED, can't handle more requests
New Client 4: ❌ WAITING (all workers busy)
```

### With gevent (Async Workers)
```
Worker 1: [SSE Client 1, SSE Client 2, SSE Client 3, ...] ← Non-blocking
Worker 2: [SSE Client 4, SSE Client 5, SSE Client 6, ...] ← Non-blocking
Worker 3: [SSE Client 7, SSE Client 8, SSE Client 9, ...] ← Non-blocking
New Client 10: ✅ ACCEPTED (workers use cooperative multitasking)
```

## Other Async Considerations

### 1. **Database Connections**
- SQLite (current): Works fine with gevent
- PostgreSQL/MySQL: Consider using connection pooling
- Recommended: `psycopg2-gevent` for PostgreSQL async support

### 2. **Cache Backend**
- Current: `LocMemCache` (in-memory)
- Production consideration: Redis with `django-redis`
- Why: Shared cache across multiple workers

### 3. **Pub/Sub for SSE**
Currently using in-memory channels (`news/sse_utils.py`):
```python
_sse_channels = defaultdict(lambda: {'subscribers': [], 'lock': threading.Lock()})
```

**Production Improvement**: Use Redis Pub/Sub
- Allows SSE messages to reach clients connected to different workers
- Install: `pip install redis channels-redis`
- Update: Replace in-memory channels with Redis channels

### 4. **Session Storage**
- Current: Database-backed sessions
- Production consideration: Redis/Memcached sessions
- Why: Faster session lookups for concurrent requests

## Testing the Setup

### 1. Install dependencies locally
```bash
pip install -r requirements.txt
```

### 2. Test with gevent locally
```bash
gunicorn --bind=127.0.0.1:8000 --workers=2 --worker-class=gevent news_api.wsgi
```

### 3. Monitor SSE connections
```bash
# In browser console
const eventSource = new EventSource('/news/stream/?last_n=5');
eventSource.onmessage = (e) => console.log(e.data);
```

### 4. Check worker status
```bash
# Should show gevent workers
ps aux | grep gunicorn
```

## Production Deployment Checklist

- [x] Add `gevent` to requirements.txt
- [x] Add `greenlet` to requirements.txt
- [x] Update startup.sh with gevent worker class
- [x] Set appropriate worker count (3 workers)
- [x] Configure timeout for long SSE connections (600s)
- [x] Set graceful timeout for clean shutdowns (30s)
- [ ] Consider Redis for cross-worker Pub/Sub (future enhancement)
- [ ] Monitor worker memory usage in production
- [ ] Set up health checks for SSE endpoint

## Troubleshooting

### SSE connections timeout
- Increase `--timeout` value
- Check Azure App Service timeout settings
- Verify firewall/proxy timeout settings

### Workers crash under load
- Increase `--workers` count
- Monitor memory usage (gevent is memory-efficient)
- Check for memory leaks in SSE handlers

### Messages not reaching all clients
- Implement Redis Pub/Sub for cross-worker messaging
- Ensure SSE channels are properly synchronized

## References
- [Gunicorn Gevent Workers](https://docs.gunicorn.org/en/stable/design.html#async-workers)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Django Channels (alternative approach)](https://channels.readthedocs.io/)
