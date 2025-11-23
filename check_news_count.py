"""
Quick script to check the number of news articles in the database.
Run with: python check_news_count.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_api.settings')
django.setup()

from news.models import News

def main():
    # Get total count
    total = News.objects.count()
    print(f"\n{'='*50}")
    print(f"📰 Total News Articles in Database: {total}")
    print(f"{'='*50}\n")
    
    # Get breakdown by category
    print("Breakdown by Category:")
    print("-" * 50)
    
    categories = {}
    for article in News.objects.all():
        category = article.category
        categories[category] = categories.get(category, 0) + 1
    
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        bar = '█' * int(percentage / 2)
        print(f"{category:15} {count:4} ({percentage:5.1f}%) {bar}")
    
    print()
    
    # Get most recent article
    latest = News.objects.order_by('-datePublished').first()
    if latest:
        print("Most Recent Article:")
        print("-" * 50)
        print(f"Headline: {latest.headline}")
        print(f"Category: {latest.category}")
        print(f"Published: {latest.datePublished}")
        print(f"Engagement: {latest.engagementLevel}")
        print()

if __name__ == '__main__':
    main()
