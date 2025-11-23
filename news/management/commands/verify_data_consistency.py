"""
Verification script to ensure SSE stream data matches database.
Run this to verify data consistency.
"""
import requests
import json
from django.core.management.base import BaseCommand
from news.models import News


class Command(BaseCommand):
    help = 'Verify that API responses match database state'

    def handle(self, *args, **options):
        base_url = "http://127.0.0.1:8000"
        
        self.stdout.write(self.style.WARNING('\n=== Database Verification ===\n'))
        
        # 1. Check database count
        db_count = News.objects.count()
        self.stdout.write(f"Total articles in database: {db_count}")
        
        # 2. Check categorized articles API
        try:
            response = requests.get(f"{base_url}/api/categorized/")
            if response.status_code == 200:
                categorized = response.json()
                api_count = sum(len(articles) for articles in categorized.values())
                self.stdout.write(f"Total articles from categorized API: {api_count}")
                
                if api_count == db_count:
                    self.stdout.write(self.style.SUCCESS('✓ Categorized API matches database'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Mismatch! DB: {db_count}, API: {api_count}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch categorized articles: {response.status_code}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching categorized articles: {e}'))
        
        # 3. Check trend analysis API
        try:
            response = requests.get(f"{base_url}/api/trends/")
            if response.status_code == 200:
                trends = response.json()
                trend_count = sum(trends.values())
                self.stdout.write(f"Total articles from trends API: {trend_count}")
                
                if trend_count == db_count:
                    self.stdout.write(self.style.SUCCESS('✓ Trends API matches database'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Mismatch! DB: {db_count}, Trends: {trend_count}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch trends: {response.status_code}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching trends: {e}'))
        
        # 4. Check category distribution
        self.stdout.write(self.style.WARNING('\n=== Category Distribution ===\n'))
        
        db_categories = {}
        for article in News.objects.all():
            category = article.category
            db_categories[category] = db_categories.get(category, 0) + 1
        
        self.stdout.write("Database categories:")
        for category, count in sorted(db_categories.items()):
            self.stdout.write(f"  {category}: {count}")
        
        try:
            response = requests.get(f"{base_url}/api/trends/")
            if response.status_code == 200:
                api_categories = response.json()
                self.stdout.write("\nAPI categories:")
                for category, count in sorted(api_categories.items()):
                    self.stdout.write(f"  {category}: {count}")
                
                # Compare
                if db_categories == api_categories:
                    self.stdout.write(self.style.SUCCESS('\n✓ Category distribution matches perfectly'))
                else:
                    self.stdout.write(self.style.WARNING('\n⚠ Category distribution differs'))
                    for category in set(list(db_categories.keys()) + list(api_categories.keys())):
                        db_val = db_categories.get(category, 0)
                        api_val = api_categories.get(category, 0)
                        if db_val != api_val:
                            self.stdout.write(f"  {category}: DB={db_val}, API={api_val}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error comparing categories: {e}'))
        
        # 5. Sample article verification
        self.stdout.write(self.style.WARNING('\n=== Sample Article Verification ===\n'))
        
        sample_article = News.objects.first()
        if sample_article:
            self.stdout.write(f"Sample article from DB:")
            self.stdout.write(f"  ID: {sample_article.id}")
            self.stdout.write(f"  Headline: {sample_article.headline[:50]}...")
            self.stdout.write(f"  Category: {sample_article.category}")
            self.stdout.write(f"  Date: {sample_article.datePublished}")
            
            # Check if it appears in categorized API
            try:
                response = requests.get(f"{base_url}/api/categorized/")
                if response.status_code == 200:
                    categorized = response.json()
                    category_articles = categorized.get(sample_article.category, [])
                    
                    found = False
                    for article in category_articles:
                        if str(article.get('_id')) == str(sample_article.id):
                            found = True
                            self.stdout.write(self.style.SUCCESS('\n✓ Sample article found in categorized API'))
                            break
                    
                    if not found:
                        self.stdout.write(self.style.ERROR('\n✗ Sample article NOT found in categorized API'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error verifying sample article: {e}'))
        
        self.stdout.write(self.style.WARNING('\n=== Verification Complete ===\n'))
