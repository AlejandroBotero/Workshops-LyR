# Quick Reference - Database Commands

## 📊 Count Articles
```bash
# Quick count
python manage.py count_news

# Detailed breakdown
python manage.py count_news --detailed
```

## 🗑️ Reset Database
```bash
# With confirmation (safe)
python manage.py reset_database

# Without confirmation (dangerous!)
python manage.py reset_database --no-confirm
```

## ✅ Verify Data
```bash
python manage.py verify_data_consistency
```

## 📥 Import from JSON
```bash
# Import
python manage.py migrate_json_to_db --file news_data.json

# Clear and import
python manage.py migrate_json_to_db --file news_data.json --clear
```

## 🔄 Common Workflows

### Fresh Start
```bash
python manage.py reset_database
python news_submitter.py
```

### Check Status
```bash
python manage.py count_news --detailed
python manage.py verify_data_consistency
```

### Development Cycle
```bash
# Reset
python manage.py reset_database --no-confirm

# Add test data
python news_submitter.py  # Ctrl+C after a few

# Verify
python manage.py count_news
```

## ⚠️ Safety Tips

- ✅ `reset_database` asks for confirmation by default
- ⚠️ `--no-confirm` skips confirmation - use carefully!
- ✅ Always verify with `count_news` after reset
- ✅ Cache is cleared automatically on reset

## 📝 Alternative: Django Shell
```bash
python manage.py shell
```
```python
from news.models import News

News.objects.count()              # Count
News.objects.all().delete()       # Delete all
News.objects.filter(category='tech').count()  # Count by category
```

## 📝 Alternative: Python Script
```bash
python check_news_count.py
```
