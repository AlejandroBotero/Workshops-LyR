from django.core.management.base import BaseCommand
from news.models import News
from django.utils import timezone
from datetime import datetime
import json
import os


class Command(BaseCommand):
    help = 'Migrate news data from JSON file to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='news_data.json',
            help='Path to the JSON file containing news data'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing news articles before importing'
        )

    def handle(self, *args, **options):
        json_file = options['file']
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.WARNING(f'File {json_file} not found. Nothing to migrate.'))
            return
        
        # Clear existing data if requested
        if options['clear']:
            count = News.objects.count()
            News.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing articles'))
        
        # Load JSON data
        with open(json_file, 'r') as file:
            try:
                news_data = json.load(file)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('Invalid JSON file'))
                return
        
        if not news_data:
            self.stdout.write(self.style.WARNING('No data found in JSON file'))
            return
        
        # Import articles
        imported = 0
        skipped = 0
        
        for article_data in news_data:
            try:
                # Parse datePublished
                date_published = article_data.get('datePublished')
                if isinstance(date_published, str):
                    try:
                        date_published = datetime.fromisoformat(date_published.replace('Z', '+00:00'))
                    except ValueError:
                        date_published = timezone.now()
                elif date_published is None:
                    date_published = timezone.now()
                
                # Create the article
                News.objects.create(
                    headline=article_data.get('headline', ''),
                    content=article_data.get('content', ''),
                    category=article_data.get('category', 'world'),
                    datePublished=date_published,
                    popularity_score=article_data.get('popularity_score', 0),
                    engagementLevel=article_data.get('engagementLevel', 'low'),
                )
                imported += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing article: {e}'))
                skipped += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported} articles, skipped {skipped}')
        )
