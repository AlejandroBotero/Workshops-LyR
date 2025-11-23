# Ollama Submitter - Usage Guide

## Overview

The `ollama_submitter.py` script uses Ollama LLM to generate realistic news articles and submit them to your API. It now supports configurable sleep time between submissions.

---

## Usage

### Default Sleep Time (1 second)
```bash
python ollama_submitter.py
```

### Custom Sleep Time
```bash
# 0.5 seconds (fast)
python ollama_submitter.py 0.5

# 2 seconds (normal)
python ollama_submitter.py 2

# 5 seconds (slow)
python ollama_submitter.py 5
```

---

## Features

### 1. **LLM-Generated Articles**
Uses Ollama with the `gemma3:1b` model to generate realistic news articles with:
- Realistic headlines
- Short content paragraphs
- Random categories (world, technology, sports, entertainment)
- Popularity scores
- Engagement levels

### 2. **Configurable Sleep Time**
- **Default**: 1 second if no parameter provided
- **Accepts**: Any positive float value
- **Validates**: Rejects negative values
- **Error Handling**: Falls back to default on invalid input

### 3. **Better Feedback**
- Shows article count
- Displays success/failure with ✓/✗ symbols
- Shows sleep time between submissions
- Graceful Ctrl+C handling

---

## Example Output

```bash
$ python ollama_submitter.py 2

======================================================================
Ollama News Submitter
======================================================================
Sleep time: 2.0 second(s)
======================================================================
Starting Ollama submission with 2.0 second(s) sleep time...
Press Ctrl+C to stop

{"category": "technology", "headline": "AI Breakthrough in Natural Language Processing", "content": "Researchers announce major advancement..."}
ollama article:  {'_id': '...', 'category': 'technology', 'headline': 'AI Breakthrough...', ...}
✓ [1] Successfully submitted article: AI Breakthrough in Natural Language Processing
Waiting for 2.0 second(s)...

{"category": "sports", "headline": "Championship Game Ends in Overtime", "content": "Exciting finish..."}
ollama article:  {'_id': '...', 'category': 'sports', 'headline': 'Championship Game...', ...}
✓ [2] Successfully submitted article: Championship Game Ends in Overtime
Waiting for 2.0 second(s)...
```

---

## Changes Made

### 1. **Added sys import**
```python
import sys
```

### 2. **Added parse_sleep_time function**
```python
def parse_sleep_time():
    if len(sys.argv) > 1:
        try:
            sleep_time = float(sys.argv[1])
            if sleep_time < 0:
                return 1.0
            return sleep_time
        except ValueError:
            return 1.0
    return 1.0
```

### 3. **Updated submit_news function**
```python
def submit_news(sleep_time=1.0):
    # Now accepts sleep_time parameter
    # Uses time.sleep(sleep_time) instead of commented code
```

### 4. **Improved main block**
```python
if __name__ == '__main__':
    sleep_time = parse_sleep_time()
    # Shows banner and sleep time
    submit_news(sleep_time)
```

### 5. **Fixed status code check**
```python
# Now accepts both 200 and 201 as success
if response.status_code in [200, 201]:
```

### 6. **Removed delete_all_data call**
- No longer deletes existing data when starting
- Articles are added to the database, not replacing

---

## Requirements

### Ollama Setup
Make sure Ollama is installed and the model is available:

```bash
# Check if Ollama is running
ollama list

# Pull the model if needed
ollama pull gemma3:1b
```

### Python Dependencies
```bash
pip install requests faker ollama
```

---

## Tips

### 1. **Stop Anytime**
Press `Ctrl+C` to stop gracefully:
```
======================================================================
Submission stopped by user
======================================================================
```

### 2. **Monitor Database**
```bash
# Terminal 1: Run submitter
python ollama_submitter.py 2

# Terminal 2: Watch count
python manage.py count_news
```

### 3. **Different Speeds**
```bash
# Very fast (for quick testing)
python ollama_submitter.py 0.1

# Normal (default)
python ollama_submitter.py 1

# Slow (to observe each article)
python ollama_submitter.py 5
```

---

## Comparison with news_submitter.py

| Feature | news_submitter.py | ollama_submitter.py |
|---------|-------------------|---------------------|
| Article Generation | Faker (random) | Ollama LLM (realistic) |
| Sleep Time | Random 1-3s | Configurable parameter |
| Article Count | 100 articles | Infinite loop |
| Status Codes | 200, 201 | 200, 201 |
| Stop Method | Ctrl+C | Ctrl+C |

---

## Troubleshooting

### Issue: Ollama not found
**Error**: `ModuleNotFoundError: No module named 'ollama'`

**Solution**:
```bash
pip install ollama
```

### Issue: Model not available
**Error**: `ollama.exceptions.ResponseError: model 'gemma3:1b' not found`

**Solution**:
```bash
ollama pull gemma3:1b
```

### Issue: Connection refused
**Error**: `requests.exceptions.ConnectionError`

**Solution**:
```bash
# Make sure Django server is running
python manage.py runserver
```

---

## Summary

**Updated Features**:
- ✅ Command-line sleep_time parameter
- ✅ Default 1 second sleep time
- ✅ Input validation
- ✅ Better user feedback
- ✅ Accepts both 200 and 201 status codes
- ✅ Removed delete_all_data call
- ✅ Graceful Ctrl+C handling

**Usage**:
```bash
# Default (1 second)
python ollama_submitter.py

# Custom sleep time
python ollama_submitter.py 2.5
```
