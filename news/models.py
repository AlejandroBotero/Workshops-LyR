from django.db import models


class News(models.Model):
    CATEGORY_CHOICES = [
        ('world', 'World'),
        ('technology', 'Technology'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('business', 'Business'),
        ('science', 'Science'),
        ('health', 'Health'),
        ('politics', 'Politics'),
    ]
    
    ENGAGEMENT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    # Core fields
    headline = models.CharField(max_length=500)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='world')
    
    # Metadata fields
    datePublished = models.DateTimeField()
    lastUpdated = models.DateTimeField(auto_now=True)
    
    # Engagement fields
    popularity_score = models.IntegerField(default=0)
    engagementLevel = models.CharField(max_length=20, choices=ENGAGEMENT_CHOICES, default='low')
    
    # Auto-managed timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datePublished']
        verbose_name_plural = 'News Articles'
        indexes = [
            models.Index(fields=['-datePublished']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.headline
    
    def to_dict(self):
        """Convert model instance to dictionary format (similar to JSON structure)"""
        return {
            '_id': str(self.id),
            'headline': self.headline,
            'content': self.content,
            'category': self.category,
            'datePublished': self.datePublished.isoformat(),
            'lastUpdated': self.lastUpdated.isoformat(),
            'popularity_score': self.popularity_score,
            'engagementLevel': self.engagementLevel,
        }
