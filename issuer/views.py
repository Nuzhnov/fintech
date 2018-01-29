# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics
import datetime
import logging
from issuer.models import Account, Transaction
from issuer.serializers import AccountSerializer, TransactionSerializer, BalanceSerializer

logger = logging.getLogger('fintech.issuer.views')


class TransactionHandler(APIView):
    def post(self, request, format=None):
        logger.info('Recived transaction: {}'.format(str(request.data)))
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Save transaction {}".format(str(serializer.data)))
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

class AccountTransactions(APIView):
    def get_object(self, account_name):
        try:
            return Account.objects.get(card_id=account_name)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, name, format=None):
        start_t = request.query_params.get("start")
        end_t = request.query_params.get("end")
        acc = self.get_object(name)
        logger.info("Requested transaction for %s from %s till %s" % \
            (acc, start_t, end_t))
        transactions = acc.transactions.\
            get_in_timeframe(start_t, end_t).\
            filter(type__exact="presentment")
        logger.info("Found transactions for time: {}".format(transactions))
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class AccountBalance(APIView):
    def get_object(self, account_name):
        try:
            return Account.objects.get(card_id=account_name)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, name, format=None):
        t_point = request.query_params.get("time")
        acc = self.get_object(name)
        balances = acc.get_balance_in_time(t_point)
        serializer = BalanceSerializer(balances)
        return Response(serializer.data)

