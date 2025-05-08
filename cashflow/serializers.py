from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import CashFlow
from .services import CashFlowValidator


class CashFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashFlow
        fields = '__all__'

    def validate(self, data: dict) -> dict:
        """Использование сервиса валидации в DRF"""
        try:
            return CashFlowValidator.validate_all(data)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
