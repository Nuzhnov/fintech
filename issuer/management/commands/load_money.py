# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from issuer.models import Account

class Command(BaseCommand):
    help = "Load modey to customer account or create it"

    def add_arguments(self, parser):
        """
        Argument parser method
        """
        parser.add_argument("cardholder", type=str, help="Card id")
        parser.add_argument("amount", type=str, help="Amount to add on account")
        parser.add_argument("currency", type=str, help="Currecny of amount")

    def handle(self, *args, **options):
        """
        Add amount to balance value of account of it exists, or create it.
        Throw exception if case of different currency.
        """
        try:
            account = Account.objects.get(card_id=options["cardholder"])
            if options["currency"] != account.currency:
                raise CommandError("Account currency is {}, not {}".\
                    format(account.currency, options["currency"]))
            account.balance = F("balance") + options["amount"]
            account.save()
            self.stdout.write(self.style.SUCCESS('Successfully updated account "%s"' % options["cardholder"]))
        except Account.DoesNotExist:
            Account.objects.create(
                card_id=options["cardholder"],
                currency=options["currency"],
                balance=options["amount"]
            )
            self.stdout.write(self.style.SUCCESS('Successfully created account "%s"' % options["cardholder"]))
