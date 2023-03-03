from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from .serializers import AccountSerializer
from .models import Account

import re
import base64


class CheckAuth:

    def decodeCredentials(self, request):
        try:
            encoded_str = request.META.get('HTTP_AUTHORIZATION', '').split('Base')[1]
            decoded_str = base64.b64decode(encoded_str).decode("utf-8")
            email, password = decoded_str.split(":")
            return {"email": email, "password": password}
        except:
            return None

    def checkAuth(self, request):
        credentials = self.decodeCredentials(request)

        if not credentials:
            return 401

        if credentials:
            if not Account.objects.filter(email=credentials["email"], password=credentials["password"]).exists():
                return 401

        return 200


class AccountService(APIView):
    serializer_class = AccountSerializer

    def get(self, request, accountId):
        return self.getAccount(request, accountId)

    def put(self, request, accountId):
        return self.updateAccount(request, accountId)

    def delete(self, request, accountId):
        return self.deleteAccount(request, accountId)

    def checkAccess(self, request, accountId):

        accountId = int(accountId)
        if not accountId or accountId <= 0:
            return 400

        if CheckAuth().checkAuth(request) == 401:
            return 401

        # Аккаунт не найден
        try:
            user = Account.objects.get(pk=accountId)
        except Account.DoesNotExist:
            return Response(status=403)

        # Обновление не своего аккаунта
        credentials = CheckAuth().decodeCredentials(request)
        if credentials["email"] != user.email or credentials["password"] != user.password:
            return Response(status=403)

        return 200

    def deleteAccount(self, request, accountId):

        # Проверка токена,account id, и собственности
        status = self.checkAccess(request, accountId)
        if status != 200:
            return Response(status=status)

        #FIXME: Аккаунт связан с животным - вернуть 400

        Account.objects.filter(pk=accountId).delete()
        return Response(status=200)


    def updateAccount(self, request, accountId):

        firstName = self.request.query_params.get('firstName', None)
        lastName = self.request.query_params.get('lastName', None)
        email = self.request.query_params.get('email', None)
        password = self.request.query_params.get('password', None)

        # Проверка полей
        if not firstName or len(firstName.split()) == 0 or not lastName or len(lastName.split()) == 0:
            return Response(status=400)
        if not email or len(email.split()) == 0 or not re.match(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?", email):
            return Response(status=400)
        if not password or len(password.split()) == 0:
            return Response(status=400)

        # Проверка токена,account id, и собственности
        status = self.checkAccess(request, accountId)
        if status != 200:
            return Response(status=status)

        # Проверка уникальности email
        if Account.objects.filter(email=email).exists():
            return Response(status=409)

        user = Account.objects.get(pk=accountId)
        user.firstName = firstName
        user.lastName = lastName
        user.email = email
        user.password = password
        user.save()

        serializer = self.serializer_class(user)
        return Response(serializer.data, status=200)

    def getAccount(self, request, accountId):

        accountId = int(accountId)
        if not accountId or accountId <= 0:
            return Response(status=400)

        if CheckAuth().checkAuth(request) == 401:
            return Response(status=401)

        if not Account.objects.filter(pk=accountId).exists():
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

        return queryset[int(start):int(start) + int(size)][::-1]

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

        # Проверка полей
        if not firstName or len(firstName.split()) == 0 or not lastName or len(lastName.split()) == 0:
            return Response(status=400)
        if not email or len(email.split()) == 0 or not re.match(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?", email):
            return Response(status=400)
        if not password or len(password.split()) == 0:
            return Response(status=400)

        # Проверка уникальности, если такой юзер уже есть, возвращаю 409
        if Account.objects.filter(email=email).exists():
            return Response(status=409)

        user = Account.objects.create(firstName=firstName, lastName=lastName, email=email, password=password)

        serializer = self.serializer_class(user)
        return Response(serializer.data, status=201)
