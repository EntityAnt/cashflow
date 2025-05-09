from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import CashFlow, Status, OperationType, Category, SubCategory
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


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    operation_type_name = serializers.CharField(source='operation_type.name', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        extra_fields = ['operation_type_name']


class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    operation_type_name = serializers.CharField(source='category.operation_type.name', read_only=True)

    class Meta:
        model = SubCategory
        fields = '__all__'
        extra_fields = ['category_name', 'operation_type_name']
