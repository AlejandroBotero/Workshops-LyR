from django.urls import path
from .views import CategorizedArticlesView, TrendAnalysisView, SubmitNewsApiView, SSEStreamView, IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('categories/', CategorizedArticlesView.as_view(), name='categorized-articles'),
    path('trends/', TrendAnalysisView.as_view(), name='trend-analysis'),
    path('submit/', SubmitNewsApiView.as_view(), name='submit-news'),
    path('stream/', SSEStreamView.as_view(), name='sse-stream'),
]
