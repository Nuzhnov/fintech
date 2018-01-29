# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
import time
from django.test import TestCase
from issuer.models import Account, Transaction, Transfer


class IssuerModelsTests(TestCase):
    """Tests for model classes"""
    @classmethod
    def setUpTestData(cls):
        Account.objects.create(
            card_id="1234LOBO",
            balance=100,
            on_hold=0,
            currency="EUR"
        )

    def setUp(self):
        self.authorize_data = {
            "type":   "authorisation", \
            "card_id": Account.objects.get(card_id="1234LOBO"), \
            "transaction_id":   "1237ZORRO", \
            "billing_amount":   "9.00", \
            "billing_currency":   "EUR", \
            "transaction_amount":   "10.00", \
            "transaction_currency":   "USD"
        }
        self.presentment_data = {
            "type":   "presentment", \
            "card_id": Account.objects.get(card_id="1234LOBO"), \
            "transaction_id":   "1237ZORRO", \
            "billing_amount":   "9.00", \
            "billing_currency":   "EUR", \
            "transaction_amount":   "10.00", \
            "transaction_currency":   "USD", \
            "settlement_amount":  "8.95", \
            "settlement_currency":  "EUR"
        }

    def test_transaction_create(self):
        """Test transaction creation"""
        Transaction.objects.create(**self.authorize_data)
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions),1)
        acc = Account.objects.get(card_id="1234LOBO")
        self.assertEqual(acc.on_hold, Decimal("9.00"))

    def test_transfers(self):
        """Test transfer creation"""
        Transaction.objects.create(**self.authorize_data)
        Transaction.objects.create(**self.presentment_data)
        transfers = Transfer.objects.all()
        acc = Account.objects.get(card_id="1234LOBO")
        self.assertEqual(len(transfers),1)
        self.assertEqual(acc.balance, Decimal("91"))
        self.assertEqual(acc.on_hold, Decimal("0.00"))
        self.assertEqual(transfers[0].debit, Decimal("9.00"))
        self.assertEqual(transfers[0].credit, Decimal("8.95"))

    def test_transactions_in_timeframe(self):
        """Test of extruction transactions for account in specific timeframe"""
        t_start = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        Transaction.objects.create(**self.authorize_data)
        Transaction.objects.create(**self.presentment_data)
        t_stop = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        transactions = Account.objects.get(card_id="1234LOBO").\
            transactions.get_in_timeframe(t_start, t_stop).\
            filter(type__exact="presentment")
        self.assertEqual(len(transactions), 1)

    def test_balance_in_time(self):
        """Test of balance extruction for account in specific time point"""
        t_first = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        Transaction.objects.create(**self.authorize_data)
        time.sleep(1)
        t_second = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        Transaction.objects.create(**self.presentment_data)
        acc = Account.objects.get(card_id="1234LOBO")
        self.assertEqual(
            acc.get_balance_in_time(t_first),
            {"balance": Decimal("100"),
            "ledger_balance": Decimal("100")}
        )
        self.assertEqual(
            acc.get_balance_in_time(t_second),
            {"balance": Decimal("100"),
            "ledger_balance": Decimal("91")}
        )
        self.assertEqual(
            acc.get_balance_in_time(),
            {"balance": Decimal("91"),
            "ledger_balance": Decimal("91")}
        )