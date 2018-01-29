# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from issuer.models import Transfer

class Command(BaseCommand):
    help = "Calculate dept to Scheme and Revenue"

    def handle(self, *args, **options):
        total_credit, total_debit = 0, 0
        transfer = Transfer.objects.get_unhandled()
        total_credit = sum([x.credit for x in transfer])
        total_debit = sum([x.debit for x in transfer])
        transfer.update(fulfilled=True)
        self.stdout.write(" dept = {}\n revenue = {}\n".format(
            total_credit,
            total_debit - total_credit
        ))