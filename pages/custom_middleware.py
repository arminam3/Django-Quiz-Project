from typing import Any


class SetThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.get('theme'):
            request.session['theme'] = 'light'
        return self.get_response(request)