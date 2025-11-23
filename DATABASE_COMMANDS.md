# Database Management Commands

## Overview

This document describes the database management commands available for the news application.

---

## Commands

### 1. `count_news` - Count Articles

Count the number of news articles in the database.

#### Basic Usage
```bash
python manage.py count_news
```

**Output**:
```
📰 Total News Articles: 193
```

#### Detailed Usage
```bash
python manage.py count_news --detailed
```

**Output**:
```
📰 Total News Articles: 193

Breakdown by Category:
  entertainment    48 ( 24.9%) ████████████
  sports           48 ( 24.9%) ████████████
  technology       49 ( 25.4%) ████████████
  world            48 ( 24.9%) ████████████

Most Recent Articles:
  1. [technology] AI Breakthrough in Natural Language Processing...
     Published: 2025-11-22 18:30
  2. [sports] Championship Game Ends in Overtime Victory...
     Published: 2025-11-22 18:25
  ...

Engagement Levels:
  Low        41 ( 21.2%)
  Medium     89 ( 46.1%)
  High       63 ( 32.6%)
```

#### Options
- `--detailed` - Show detailed breakdown by category, recent articles, and engagement stats

---

### 2. `reset_database` - Reset Database

Delete all news articles from the database.

#### Basic Usage (with confirmation)
```bash
python manage.py reset_database
```

**Interactive Prompt**:
```
📊 Current Database State:
   Total Articles: 193

   By Category:
     - entertainment: 48
     - sports: 48
     - technology: 49
     - world: 48

⚠️  WARNING: This will DELETE all 193 articles!

   Type "yes" to confirm: 
```

Type `yes` to confirm deletion, or anything else to cancel.

#### Skip Confirmation
```bash
python manage.py reset_database --no-confirm
```

**Use with caution!** This will delete all articles without asking.

#### Keep Cache
```bash
python manage.py reset_database --keep-cache
```

Delete articles but keep the cache (not recommended).

#### Options
- `--no-confirm` - Skip confirmation prompt (dangerous!)
- `--keep-cache` - Don't clear caches after deletion

---

### 3. `verify_data_consistency` - Verify Data

Verify that API responses match the database state.

#### Usage
```bash
python manage.py verify_data_consistency
```

**Output**:
```
=== Database Verification ===

Total articles in database: 193
Total articles from categorized API: 193
✓ Categorized API matches database

Total articles from trends API: 193
✓ Trends API matches database

=== Category Distribution ===

Database categories:
  entertainment: 48
  sports: 48
  technology: 49
  world: 48

API categories:
  entertainment: 48
  sports: 48
  technology: 49
  world: 48

✓ Category distribution matches perfectly

=== Sample Article Verification ===

Sample article from DB:
  ID: 1
  Headline: AI Breakthrough in Natural Language Processing...
  Category: technology
  Date: 2025-11-22 18:30:00+00:00

✓ Sample article found in categorized API

=== Verification Complete ===
```

---

### 4. `migrate_json_to_db` - Import from JSON

Migrate news data from JSON file to database.

#### Basic Usage
```bash
python manage.py migrate_json_to_db --file news_data.json
```

#### Clear Database First
```bash
python manage.py migrate_json_to_db --file news_data.json --clear
```

**Warning**: `--clear` will delete all existing articles before importing!

#### Options
- `--file` - Path to JSON file (default: `news_data.json`)
- `--clear` - Delete all existing articles before importing

---

## Common Workflows

### Workflow 1: Fresh Start

Reset database and start fresh:

```bash
# 1. Reset database
python manage.py reset_database

# 2. Verify it's empty
python manage.py count_news

# 3. Start submitting new articles
python news_submitter.py
```

### Workflow 2: Import from JSON

Import articles from a JSON file:

```bash
# 1. Reset database (optional)
python manage.py reset_database --no-confirm

# 2. Import from JSON
python manage.py migrate_json_to_db --file news_data.json

# 3. Verify import
python manage.py count_news --detailed
```

### Workflow 3: Verify Data Integrity

Check that everything is consistent:

```bash
# 1. Count articles
python manage.py count_news

# 2. Verify consistency
python manage.py verify_data_consistency

# 3. Check API endpoints
curl http://127.0.0.1:8000/api/trends/
```

### Workflow 4: Development Reset

Quick reset for development:

```bash
# Reset without confirmation
python manage.py reset_database --no-confirm

# Submit test data
python news_submitter.py
# (Press Ctrl+C after a few articles)

# Verify
python manage.py count_news
```

---

## Safety Features

### Confirmation Prompts

The `reset_database` command requires confirmation by default:

```bash
python manage.py reset_database
# Prompts: Type "yes" to confirm
```

To skip (use carefully):
```bash
python manage.py reset_database --no-confirm
```

### Current State Display

Before deletion, the command shows:
- Total article count
- Breakdown by category
- Clear warning message

### Verification

After reset:
- Confirms deletion count
- Verifies database is empty
- Reports any remaining articles

---

## Alternative Methods

### Using Django Shell

```bash
python manage.py shell
```

```python
from news.models import News

# Count articles
News.objects.count()

# Delete all articles
News.objects.all().delete()

# Count by category
News.objects.filter(category='technology').count()

# Get recent articles
News.objects.order_by('-datePublished')[:10]
```

### Using Python Script

```bash
python check_news_count.py
```

This standalone script shows article count and breakdown.

---

## Best Practices

### 1. Always Verify After Reset
```bash
python manage.py reset_database
python manage.py count_news  # Should show 0
```

### 2. Clear Cache After Reset
```bash
# Cache is cleared by default
python manage.py reset_database

# Or manually
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### 3. Backup Before Reset

If you have important data:
```bash
# Export to JSON (create this command if needed)
python manage.py dumpdata news.News > backup.json

# Reset
python manage.py reset_database

# Restore if needed
python manage.py loaddata backup.json
```

### 4. Use --detailed for Insights
```bash
# See what you're deleting
python manage.py count_news --detailed

# Then reset
python manage.py reset_database
```

---

## Troubleshooting

### Issue: Command Not Found

**Error**: `Unknown command: 'reset_database'`

**Solution**: Make sure the file exists:
```bash
ls news/management/commands/reset_database.py
```

If missing, the command file wasn't created properly.

### Issue: Articles Not Deleting

**Error**: "Warning: X articles still remain!"

**Solution**:
```bash
# Try manual deletion
python manage.py shell
>>> from news.models import News
>>> News.objects.all().delete()
>>> News.objects.count()  # Should be 0
```

### Issue: Cache Not Clearing

**Symptom**: API still shows old data after reset

**Solution**:
```bash
# Manually clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

Or restart the server:
```bash
# Stop server (Ctrl+C)
python manage.py runserver
```

---

## Summary

| Command | Purpose | Confirmation | Clears Cache |
|---------|---------|--------------|--------------|
| `count_news` | Count articles | No | No |
| `count_news --detailed` | Detailed breakdown | No | No |
| `reset_database` | Delete all articles | Yes | Yes |
| `reset_database --no-confirm` | Delete without prompt | No | Yes |
| `reset_database --keep-cache` | Delete, keep cache | Yes | No |
| `verify_data_consistency` | Check data integrity | No | No |
| `migrate_json_to_db` | Import from JSON | No | No |

**Remember**: Always use `--no-confirm` carefully - it will delete all data without asking!
