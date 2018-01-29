from rest_framework import serializers, fields
from issuer.models import Transaction, Account, AUTHORISATION, PRESENTMENT
from decimal import Decimal


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_field = ("id",)
    
    def validate(self, data):
        if data.get("type") == AUTHORISATION:
            if not Account.objects.\
            get(card_id=data.get("card_id")).\
            check_funds(data.get("billing_amount")):
                raise serializers.ValidationError("No sufficient funds")
        else:
            if not Transaction.objects.filter(
                transaction_id=data.get("transaction_id"), 
                type=AUTHORISATION, 
                card_id=data.get("card_id")
            ):
                raise serializers.ValidationError("Not performed autorization for this transaction!")
        return data

    def create(self, validated_data):
        return Transaction.objects.create(**validated_data)


class BalanceSerializer(serializers.Serializer):
    """Simple serializer for balance requests"""
    ledger_balance = fields.DecimalField(11, 2)
    balance = fields.DecimalField(11, 2)


