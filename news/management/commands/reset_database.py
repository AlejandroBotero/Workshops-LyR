"""
Management command to reset the news database.
Deletes all news articles and clears caches.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from news.models import News
from news.services import CacheService


class Command(BaseCommand):
    help = 'Reset the news database by deleting all articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--keep-cache',
            action='store_true',
            help='Keep cache (do not clear)',
        )

    def handle(self, *args, **options):
        # Get current count
        current_count = News.objects.count()
        
        if current_count == 0:
            self.stdout.write(self.style.WARNING('\n⚠️  Database is already empty (0 articles)\n'))
            return
        
        # Show current state
        self.stdout.write(self.style.WARNING(f'\n📊 Current Database State:'))
        self.stdout.write(f'   Total Articles: {current_count}')
        
        # Show breakdown by category
        categories = {}
        for article in News.objects.all():
            category = article.category
            categories[category] = categories.get(category, 0) + 1
        
        self.stdout.write('\n   By Category:')
        for category, count in sorted(categories.items()):
            self.stdout.write(f'     - {category}: {count}')
        
        # Confirmation prompt
        if not options['no_confirm']:
            self.stdout.write(self.style.ERROR(f'\n⚠️  WARNING: This will DELETE all {current_count} articles!'))
            confirm = input('\n   Type "yes" to confirm: ')
            
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('\n❌ Reset cancelled.\n'))
                return
        
        # Delete all articles
        self.stdout.write(self.style.WARNING('\n🗑️  Deleting articles...'))
        deleted_count, _ = News.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} articles'))
        
        # Clear cache
        if not options['keep_cache']:
            self.stdout.write(self.style.WARNING('\n🧹 Clearing caches...'))
            
            # Clear specific news caches
            CacheService.invalidate_all()
            
            # Clear all cache (optional, more thorough)
            cache.clear()
            
            self.stdout.write(self.style.SUCCESS('✓ Caches cleared'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Cache kept (use --no-keep-cache to clear)'))
        
        # Verify
        remaining = News.objects.count()
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Database reset complete!'))
            self.stdout.write(self.style.SUCCESS('   All articles deleted successfully.\n'))
        else:
            self.stdout.write(self.style.ERROR(f'\n⚠️  Warning: {remaining} articles still remain!\n'))
