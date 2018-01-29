# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from issuer.models import Account


class TransactionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Account.objects.create(card_id="1234LOBO",
            balance=100,
            on_hold=0,
            currency="EUR"
        )    

    def setUp(self):
        self.client = APIClient()
        self.test_data = {"type":   "authorisation", \
            "card_id":   "1234LOBO", \
            "transaction_id":   "1237ZORRO", \
            "merchant_name":   "SNEAKERS   R   US", \
            "merchant_country":   "US", \
            "merchant_mcc":   "5139", \
            "billing_amount":   "9.00", \
            "billing_currency":   "EUR", \
            "transaction_amount":   "10.00", \
            "transaction_currency":   "USD"}
        self.test_data_wrong = {"type":   "authorisation", \
            "card_id":   "1234LOBO", \
            "transaction_id":   "1237ZORRO", \
            "merchant_name":   "SNEAKERS   R   US", \
            "merchant_country":   "US", \
            "merchant_mcc":   "5139", \
            "billing_amount":   "900.00", \
            "billing_currency":   "EUR", \
            "transaction_amount":   "1000.00", \
            "transaction_currency":   "USD"}
        self.test_data_presentment = {"type":   "presentment", \
            "card_id":   "1234LOBO", \
            "transaction_id":   "1237ZORRO", \
            "merchant_name":   "SNEAKERS   R   US", \
            "merchant_country":   "US", \
            "merchant_mcc":   "5139", \
            "billing_amount":   "9.00", \
            "billing_currency":   "EUR", \
            "transaction_amount":   "10.00", \
            "transaction_currency":   "USD", \
            "settlement_amount":  "8.95", \
            "settlement_currency":  "EUR"}

    def test_transactions(self):
        start_t = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        r = self.client.post('/', data=self.test_data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(Account.objects.get(card_id="1234LOBO").on_hold,
            Decimal(9.00))
        r = self.client.post('/', data=self.test_data_presentment)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(Account.objects.get(card_id="1234LOBO").on_hold,
            Decimal(0.00))
        self.assertEqual(Account.objects.get(card_id="1234LOBO").balance,
            Decimal(91.00).quantize(Decimal('0.01')))
        end_t = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        r = self.client.get('/accounts/1234LOBO/transactions',
            data={"start": start_t, "end": end_t})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_auth_transactions_negative(self):
        r = self.client.post('/', data=self.test_data_wrong)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.test_data["settlement_amount"] = "8.91"
        self.test_data["settlement_currency"] = "EUR"
        self.test_data["type"] = "presentment"
        r = self.client.post('/', data=self.test_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_balance_in_time(self):
        r = self.client.post('/', data=self.test_data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        first = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        r = self.client.post('/', data=self.test_data_presentment)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        second = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        f = self.client.get('/accounts/1234LOBO/balance',
            data={"time": first})
        self.assertEqual(f.status_code, status.HTTP_200_OK) 
        self.assertDictEqual(f.data, 
            {"balance": "100.00",
            "ledger_balance": "91.00"}
        )
        f = self.client.get('/accounts/1234LOBO/balance',
            data={"time": second})
        self.assertEqual(f.status_code, status.HTTP_200_OK) 
        self.assertDictEqual(f.data, 
            {"balance": "91.00",
            "ledger_balance": "91.00"}
        )


