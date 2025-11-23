"""
Management command to count news articles in the database.
"""
from django.core.management.base import BaseCommand
from news.models import News


class Command(BaseCommand):
    help = 'Count the number of news articles in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown by category',
        )

    def handle(self, *args, **options):
        # Get total count
        total_count = News.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'\n📰 Total News Articles: {total_count}\n'))
        
        # Show detailed breakdown if requested
        if options['detailed']:
            self.stdout.write(self.style.WARNING('Breakdown by Category:'))
            
            categories = News.objects.values_list('category', flat=True).distinct()
            
            for category in sorted(categories):
                count = News.objects.filter(category=category).count()
                percentage = (count / total_count * 100) if total_count > 0 else 0
                
                # Create a simple bar chart
                bar_length = int(percentage / 2)  # Scale to max 50 chars
                bar = '█' * bar_length
                
                self.stdout.write(f'  {category:15} {count:4} ({percentage:5.1f}%) {bar}')
            
            # Show recent articles
            self.stdout.write(self.style.WARNING('\nMost Recent Articles:'))
            recent = News.objects.all().order_by('-datePublished')[:5]
            
            for i, article in enumerate(recent, 1):
                headline = article.headline[:60] + '...' if len(article.headline) > 60 else article.headline
                self.stdout.write(f'  {i}. [{article.category}] {headline}')
                self.stdout.write(f'     Published: {article.datePublished.strftime("%Y-%m-%d %H:%M")}')
            
            # Show engagement stats
            self.stdout.write(self.style.WARNING('\nEngagement Levels:'))
            for level in ['low', 'medium', 'high']:
                count = News.objects.filter(engagementLevel=level).count()
                percentage = (count / total_count * 100) if total_count > 0 else 0
                self.stdout.write(f'  {level.capitalize():8} {count:4} ({percentage:5.1f}%)')
        
        self.stdout.write('')  # Empty line at the end
