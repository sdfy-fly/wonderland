from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from .serializers import AccountSerializer
from .models import Account

import re
import base64


class CheckAuth:

    def __decodeCredentials(self, request):
        try:
            encoded_str = request.META.get('HTTP_AUTHORIZATION', '').split('Base')[1]
            decoded_str = base64.b64decode(encoded_str).decode("utf-8")
            email, password = decoded_str.split(":")
            return {"email": email, "password": password}
        except:
            return None

    def checkAuth(self, request):
        credentials = self.__decodeCredentials(request)

        if not credentials:
            return 401

        if credentials:
            if not Account.objects.filter(email=credentials["email"], password=credentials["password"]).exists():
                return 401

        return 200


class GetAccount(APIView):
    serializer_class = AccountSerializer

    def get(self, request, accountId):
        return self.getAccount(request, accountId)

    def getAccount(self, request, accountId):

        accountId = int(accountId)
        if not accountId or accountId <= 0:
            return Response(status=400)

        if CheckAuth().checkAuth(request) == 401:
            return Response(status=401)

        user = Account.objects.filter(pk=accountId).exists()
        if not user:
            return Response(status=404)

        serializer = self.serializer_class(Account.objects.get(pk=accountId))
        return Response(serializer.data, status=200)


class SearchAccount(generics.ListAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        queryset = Account.objects.all()
        firstName = self.request.query_params.get('firstName', None)
        lastName = self.request.query_params.get('lastName', None)
        email = self.request.query_params.get('email', None)
        start = self.request.query_params.get('from', 0)
        size = self.request.query_params.get('size', 10)

        if firstName:
            queryset = queryset.filter(Q(firstName__icontains=firstName))
        if lastName:
            queryset = queryset.filter(Q(lastName__icontains=lastName))
        if email:
            queryset = queryset.filter(Q(email__icontains=email))

        return queryset[int(start):int(start) + int(size)]

    def get(self, request, *args, **kwargs):
        start = self.request.query_params.get('from', 0)
        size = self.request.query_params.get('size', 10)
        if int(start) < 0 or int(size) <= 0:
            return Response(status=400)

        if CheckAuth().checkAuth(request) == 401:
            return Response(status=401)

        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=200)


class Registration(APIView):
    serializer_class = AccountSerializer

    def post(self, request):

        firstName: str = request.data["firstName"]
        lastName: str = request.data["lastName"]
        email: str = request.data["email"]
        password: str = request.data["password"]

        return self.signUp(request, firstName, lastName, email, password)

    def signUp(self, request, firstName: str, lastName: str, email: str, password: str):

        # Проверка авторизации, если пользователь не авторизован возвращаю 403
        if CheckAuth().checkAuth(request) == 200:
            return Response(status=403)

        if not firstName or len(firstName.split()) == 0 or \
                not lastName or len(lastName.split()) == 0 or \
                not email or len(email.split()) == 0 or \
                not re.match(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?", email) or \
                not password or len(password.split()) == 0:
            return Response(status=400)

        # Проверка уникальности, если такой юзер уже есть, возвращаю 409
        if Account.objects.filter(email=email).exists():
            return Response(status=409)

        user = Account.objects.create(firstName=firstName, lastName=lastName, email=email, password=password)

        serializer = self.serializer_class(user)
        return Response(serializer.data, status=201)
