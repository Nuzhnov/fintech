from django.conf.urls import url
from django.contrib import admin
from rest_framework.documentation import include_docs_urls
from issuer import views

urlpatterns = [
    url(r'^accounts/(?P<name>[a-zA-Z0-9]+)/transactions', views.AccountTransactions.as_view()),
    url(r'^accounts/(?P<name>[a-zA-Z0-9]+)/balance', views.AccountBalance.as_view()),
    url(r'', views.TransactionHandler.as_view()),
    url(r'^docs/', include_docs_urls(title='Card issuer API'))
]
