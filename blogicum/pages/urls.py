"""pages URL Configuration."""
from django.urls import path

from .views import AboutView, RulesView
# from django.views.generic import TemplateView

app_name = 'pages'

# handler404 = 'pages.views.page_not_found'
# handler500 = 'pages.views.server_error'

urlpatterns = [
    path('about/', AboutView.as_view(), name='about'),
    path('rules/', RulesView.as_view(), name='rules'),
]
