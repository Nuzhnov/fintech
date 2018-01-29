# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from decimal import Decimal
from django.db import models

logger = logging.getLogger('fintech.issuer.models')


AUTHORISATION = "authorisation"
PRESENTMENT = "presentment"
TRANSACTION_CHOICES = sorted((i, i) for i in [AUTHORISATION, PRESENTMENT])

class Account(models.Model):
    """Model describes funds on account"""
    card_id = models.CharField(max_length=100, primary_key=True)
    balance = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    on_hold = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="EUR")

    def avaliable_balance(self):
        """
        Get avaliable balance whithout reserved funds
        """
        return self.balance - self.on_hold

    def check_funds(self, amount):
        """
        Check if new payment avaliable for account
        """
        if self.avaliable_balance() - Decimal(amount) >= 0:
            return True

    def authorize(self, amount):
        """
        Authorize funds (move it on hold)
        """
        self.on_hold = models.F("on_hold") + amount
        self.save()

    def settle(self, auth_billing_amount, presentment_billing_amount):
        """
        Perform payment transefer from account
        """
        self.on_hold = models.F("on_hold") - auth_billing_amount
        self.balance = models.F("balance") - presentment_billing_amount
        self.save()

    def get_balance_in_time(self, timestamp=None):
        """
        Calculate 'balance' and 'on_hold' of account
        at specific point of time.
        """
        tr_ids = set()
        balance = self.balance
        on_hold = self.on_hold
        logger.debug("Requested balance in time: %s" % timestamp)
        if not timestamp:
            return {"balance":balance, "ledger_balance": balance - on_hold}
        transactions = self.transactions.get_in_timeframe(start=timestamp).order_by('id').reverse()
        logger.debug("Requested transactions %s" % transactions)
        for tr in transactions:
            if tr.transaction_id not in tr_ids:
                if tr.type == "presentment":
                    balance += tr.billing_amount
                    on_hold += tr.billing_amount
                else:
                    on_hold -= tr.billing_amount
                tr_ids.add(tr.transaction_id)
            else:
                on_hold -= tr.billing_amount
        return {"balance":balance, "ledger_balance": balance - on_hold}
    
    def __unicode__(self):
        return self.card_id

class TransactionManager(models.Manager):
    """Model manager for transations"""
    def get_in_timeframe(self, start=None, end=None):
        """Returns all transactions in defined timeframe"""
        start = models.DateTimeField().to_python(start)
        end = models.DateTimeField().to_python(end)
        logger.debug("Requested transaction from %s to %s" % (start, end))
        if not (start or end):
            return self.all()
        elif not end:
            return self.filter(date__gte=start)
        elif not start:
            return self.filter(date__lte=end)
        else:
            return self.filter(date__gte=start, date__lte=end)

class Transaction(models.Model):
    """Describes flow of money on account"""
    transaction_id = models.CharField(max_length=100)
    type = models.CharField(choices=TRANSACTION_CHOICES, default=AUTHORISATION, max_length=100)
    card_id = models.ForeignKey(Account, related_name="transactions", to_field="card_id")
    billing_amount = models.DecimalField(max_digits=11, decimal_places=2)
    billing_currency = models.CharField(max_length=3)
    transaction_amount = models.DecimalField(max_digits=11, decimal_places=2)
    transaction_currency = models.CharField(max_length=3)
    settlement_amount = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    settlement_currency = models.CharField(max_length=3, default="")
    date = models.DateTimeField(auto_now_add=True)
    objects = TransactionManager()

    def save(self, *args, **kwargs):
        """
        Redefined 'save' method.
        In case of 'authorization' transaction perfroms additionally
        hold off amount on account.
        In case of 'presentment' - calls 'settle' method on account
        """
        logger.debug("Going to save {} transaction {} for card {} on {} {}... ".\
        format(self.type, self.transaction_id, self.card_id, self.billing_amount, self.billing_currency))
        if self.type == AUTHORISATION:
            self.card_id.authorize(self.billing_amount)
        else:
            auth_amount = Transaction.objects.\
            get(transaction_id=self.transaction_id).billing_amount
            self.card_id.settle(auth_amount, self.billing_amount)
            Transfer.objects.create(
                credit=self.settlement_amount,
                debit=self.billing_amount,
                currency=self.billing_currency
            )
        return super(Transaction, self).save(*args, **kwargs)
    
    class Meta:
        unique_together = ("transaction_id", "type", "card_id")

    def __unicode__(self):
        return self.transaction_id + self.type + self.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


class TransferManager(models.Manager):
    """Manager to get only unhandled transfers"""
    
    def get_unhandled(self):
        """
        Get not fulfilled transfer operations
        """
        return self.filter(fulfilled=False)


class Transfer(models.Model):
    """Describes credit and debit on each transaction"""

    credit = models.DecimalField(max_digits=11, decimal_places=2)
    debit = models.DecimalField(max_digits=11, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    currency = models.CharField(max_length=3)
    objects = TransferManager()

    def __unicode__(self):
        return str(self.pk)


