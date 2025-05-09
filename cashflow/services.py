from datetime import date
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.utils import timezone


class CashFlowValidator:
    """
    Сервисный слой для валидации данных CashFlow
    """

    @staticmethod
    def validate_date(value: date) -> date:
        """Валидация даты"""
        if value > timezone.now().date():
            raise ValidationError("Дата не может быть в будущем")
        return value

    @staticmethod
    def validate_amount(value: float) -> float:
        """Валидация суммы"""
        if value <= 0:
            raise ValidationError("Сумма должна быть положительной")
        if value > 1000000000:
            raise ValidationError("Сумма слишком больная")
        return round(value, 2)

    @staticmethod
    def validate_category_relations(
            category: 'Category',
            subcategory: 'SubCategory'
    ) -> None:
        """Валидация связей категория-подкатегория"""
        if category and subcategory and subcategory.category != category:
            raise ValidationError(
                "Выбранная подкатегория не принадлежит выбранной категории"
            )

    @classmethod
    def validate_all(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Комплексная валидация всех данных
        Args:
            data: Словарь с данными для валидации
        Returns:
            Валидированные и обработанные данные
        Raises:
            ValidationError: При ошибках валидации
        """
        validated_data = data.copy()

        # Валидация даты
        if 'date' in validated_data:
            validated_data['date'] = cls.validate_date(validated_data['date'])

        # Валидация суммы
        if 'amount' in validated_data:
            validated_data['amount'] = cls.validate_amount(validated_data['amount'])

        # Валидация связей
        if all(key in validated_data for key in ['category', 'subcategory']):
            cls.validate_category_relations(
                validated_data['category'],
                validated_data['subcategory']
            )

        return validated_data


