from django.urls import path, re_path
from .views import Registration, GetAccount, SearchAccount

urlpatterns = [
    re_path(r'^accounts/(?P<accountId>-?\d+)/$', GetAccount.as_view()),
    path('accounts/search', SearchAccount.as_view()),
    path('registration', Registration.as_view()),
]
