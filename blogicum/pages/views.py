from django.views import View
from django.shortcuts import render


def server_error(request):
    # Можно добавить логику для отладки, если нужно
    return render(request, 'pages/500.html', status=500)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем.
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


class AboutView(View):
    def get(self, request):
        return render(request, 'pages/about.html')


class RulesView(View):
    def get(self, request):
        return render(request, 'pages/rules.html')
