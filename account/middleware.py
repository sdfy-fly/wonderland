import base64

from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate, login


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not request.user.is_authenticated:

            try:
                encoded_str = request.META.get('HTTP_AUTHORIZATION', '').split('Base')[1]
                decoded_str = base64.b64decode(encoded_str).decode("utf-8")
                email, password = decoded_str.split(":")
            except:
                return HttpResponse('Unauthorized', status=401)

            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)

        response = self.get_response(request)
        return response
