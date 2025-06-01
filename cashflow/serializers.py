from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import CashFlow, Category, OperationType, Status, SubCategory
from .services.validators import (BaseValidator, CashFlowValidator,
                                  CategoryValidator, OperationTypeValidator,
                                  SubCategoryValidator)


class CashFlowSerializer(serializers.ModelSerializer):
    """Сериализатор для денежных потоков с комплексной валидацией"""

    class Meta:
        model = CashFlow
        fields = "__all__"

    def validate(self, data: dict[str, any]) -> dict[str, any]:
        """Основная валидация через сервисный слой"""
        try:
            return CashFlowValidator.validate_all(data)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict or str(e))


class StatusSerializer(serializers.ModelSerializer):
    """Сериализатор статусов с проверкой уникальности"""

    class Meta:
        model = Status
        fields = "__all__"

    def validate_name(self, value: str) -> str:
        """Делегируем проверку уникальности сервисному слою"""
        try:
            return BaseValidator.validate_unique_name(Status, value, self.instance)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))


class OperationTypeSerializer(serializers.ModelSerializer):
    """Сериализатор типов операций"""

    class Meta:
        model = OperationType
        fields = "__all__"

    def validate_name(self, value: str) -> str:
        """Валидация имени через сервисный слой"""
        try:
            return OperationTypeValidator.validate_name(value, self.instance)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий с расширенной валидацией"""

    operation_type_name = serializers.CharField(
        source="operation_type.name", read_only=True
    )

    class Meta:
        model = Category
        fields = "__all__"
        extra_fields = ["operation_type_name"]

    def validate(self, attrs: dict[str, any]) -> dict[str, any]:
        """Комплексная валидация категории"""
        name = attrs.get("name")
        operation_type = attrs.get("operation_type")

        if name and operation_type:
            try:
                attrs["name"] = CategoryValidator.validate_name(
                    name, operation_type, self.instance
                )
            except ValidationError as e:
                raise serializers.ValidationError({"name": str(e)})

        return attrs


class SubCategorySerializer(serializers.ModelSerializer):
    """Сериализатор подкатегорий с проверкой связей"""

    category_name = serializers.CharField(source="category.name", read_only=True)
    operation_type_name = serializers.CharField(
        source="category.operation_type.name", read_only=True
    )

    class Meta:
        model = SubCategory
        fields = "__all__"
        extra_fields = ["category_name", "operation_type_name"]

    def validate(self, attrs: dict[str, any]) -> dict[str, any]:
        """Валидация подкатегории через сервисный слой"""
        name = attrs.get("name")
        category = attrs.get("category")

        if name and category:
            try:
                attrs["name"] = SubCategoryValidator.validate_name(
                    name, category, self.instance
                )
            except ValidationError as e:
                raise serializers.ValidationError({"name": str(e)})

        return attrs
