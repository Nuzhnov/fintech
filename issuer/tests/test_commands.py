from datetime import datetime
from decimal import Decimal
import time
from django.test import TestCase
from django.core.management import call_command
from issuer.models import Account, Transaction, Transfer
from issuer.management.commands import calculate, load_money

class CommandsTests(TestCase):
    """Tests for custom commands"""
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
    
    def test_load_money(self):
        """Test for load_money command"""
        args = ["1235LOBO", 100, "EUR"]
        call_command("load_money", *args, **{})
        self.assertEqual(
            len(Account.objects.filter(card_id="1235LOBO")),
            1
        )
        self.assertEqual(
            Account.objects.get(card_id="1235LOBO").balance,
            Decimal("100")
        )
        call_command("load_money", *args, **{})
        self.assertEqual(
            Account.objects.get(card_id="1235LOBO").balance,
            Decimal("200")
        )

    def test_calculate(self):
        """Test for calculate command"""
        Transaction.objects.create(**self.authorize_data)
        Transaction.objects.create(**self.presentment_data)
        self.assertEqual(
            len(Transfer.objects.get_unhandled()),
            1
        )
        call_command("calculate")
        self.assertEqual(
            len(Transfer.objects.get_unhandled()),
            0
        )


