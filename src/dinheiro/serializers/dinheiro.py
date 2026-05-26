from rest_framework import serializers
from ..models.dinheiro import BankAccount, Transaction

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "firm", "name", "account_type", "provider_name", "initial_balance", "current_balance", "created_at"]
        read_only_fields = ["id", "firm", "current_balance", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            "id", "account", "account_name", "description", "amount", 
            "transaction_type", "date", "expense_installment", 
            "fee_installment", "external_transaction_id", "is_reconciled", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if attrs.get("expense_installment") and attrs.get("fee_installment"):
            raise serializers.ValidationError("Uma transação não pode estar vinculada a uma despesa e a um honorário simultaneamente.")
        return attrs