from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('headline', 'category', 'datePublished', 'popularity_score', 'engagementLevel')
    list_filter = ('category', 'engagementLevel', 'datePublished')
    search_fields = ('headline', 'content')
    date_hierarchy = 'datePublished'
    ordering = ('-datePublished',)

