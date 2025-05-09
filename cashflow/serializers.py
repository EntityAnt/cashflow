from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CashFlow, Status, OperationType, Category, SubCategory
from .services import CashFlowValidator
from typing import Dict, Any, Type


class CashFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model: Type[CashFlow] = CashFlow
        fields: str = '__all__'

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных с использованием сервисного слоя.

        Args:
            data: Входные данные для валидации

        Returns:
            Валидированные данные

        Raises:
            serializers.ValidationError: При ошибках валидации
        """
        try:
            return CashFlowValidator.validate_all(data)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages) from e


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model: Type[Status] = Status
        fields: str = '__all__'

    def validate_name(self, value: str) -> str:
        """
        Валидация названия статуса.

        Args:
            value: Значение поля name

        Returns:
            Проверенное значение

        Raises:
            serializers.ValidationError: Если статус с таким именем уже существует
        """
        if Status.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Статус с таким названием уже существует")
        return value


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model: Type[OperationType] = OperationType
        fields: str = '__all__'

    def validate_name(self, value: str) -> str:
        """
        Валидация названия типа операции.

        Args:
            value: Значение поля name

        Returns:
            Проверенное значение

        Raises:
            serializers.ValidationError: Если тип операции с таким именем уже существует
        """
        if OperationType.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Тип операции с таким названием уже существует")
        return value


class CategorySerializer(serializers.ModelSerializer):
    operation_type_name: serializers.CharField = serializers.CharField(
        source='operation_type.name',
        read_only=True,
        help_text="Название типа операции"
    )

    class Meta:
        model: Type[Category] = Category
        fields: list[str] = '__all__'
        extra_fields: list[str] = ['operation_type_name']

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация связки категория + тип операции.

        Args:
            attrs: Атрибуты для валидации

        Returns:
            Проверенные атрибуты

        Raises:
            serializers.ValidationError: Если категория с таким именем уже существует для данного типа
        """
        name = attrs.get('name')
        operation_type = attrs.get('operation_type')

        if name and operation_type:
            if Category.objects.filter(
                    name__iexact=name,
                    operation_type=operation_type
            ).exists():
                raise serializers.ValidationError(
                    {"name": "Категория с таким названием уже существует для этого типа операции"}
                )
        return attrs


class SubCategorySerializer(serializers.ModelSerializer):
    category_name: serializers.CharField = serializers.CharField(
        source='category.name',
        read_only=True,
        help_text="Название родительской категории"
    )
    operation_type_name: serializers.CharField = serializers.CharField(
        source='category.operation_type.name',
        read_only=True,
        help_text="Название типа операции родительской категории"
    )

    class Meta:
        model: Type[SubCategory] = SubCategory
        fields: list[str] = '__all__'
        extra_fields: list[str] = ['category_name', 'operation_type_name']

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация связки подкатегория + категория.

        Args:
            attrs: Атрибуты для валидации

        Returns:
            Проверенные атрибуты

        Raises:
            serializers.ValidationError: Если подкатегория с таким именем уже существует для данной категории
        """
        name = attrs.get('name')
        category = attrs.get('category')

        if name and category:
            if SubCategory.objects.filter(
                    name__iexact=name,
                    category=category
            ).exists():
                raise serializers.ValidationError(
                    {"name": "Подкатегория с таким названием уже существует для этой категории"}
                )
        return attrs
