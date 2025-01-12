from django.shortcuts import render
from django.views import View


def server_error(request):
    return render(request, 'pages/500.html', status=500)


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


class AboutView(View):
    def get(self, request):
        return render(request, 'pages/about.html')


class RulesView(View):
    def get(self, request):
        return render(request, 'pages/rules.html')
