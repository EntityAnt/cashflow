from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from ..models import OperationType, Category, SubCategory


class BaseValidator:
    """Базовый класс для всех валидаторов"""

    @classmethod
    def validate_unique_name(cls, model, name: str, instance=None) -> str:
        """Проверка уникальности имени с учетом регистра"""
        qs = model.objects.filter(name__iexact=name)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ValidationError(f"{model.__name__} с таким названием уже существует")
        return name.strip()


class CashFlowValidator:
    """Валидатор для операций денежного потока"""

    @staticmethod
    def validate_date(value: date) -> date:
        """Проверяем, что дата не в будущем"""
        if value > timezone.now().date():
            raise ValidationError("Дата не может быть в будущем")
        return value

    @staticmethod
    def validate_amount(value: float) -> float:
        """Валидация суммы (положительная и разумный предел)"""
        if value <= 0:
            raise ValidationError("Сумма должна быть положительной")
        if value > 1000000000:
            raise ValidationError("Сумма превышает максимально допустимую")
        return round(value, 2)

    @staticmethod
    def validate_category_relations(category, subcategory) -> None:
        """Проверка соответствия категории и подкатегории"""
        if category and subcategory and subcategory.category != category:
            raise ValidationError("Подкатегория не принадлежит выбранной категории")

    @classmethod
    def validate_all(cls, data: dict[str, any]) -> dict[str, any]:
        """Комплексная валидация всех данных CashFlow"""
        validated_data = data.copy()

        if "date" in validated_data:
            validated_data["date"] = cls.validate_date(validated_data["date"])

        if "amount" in validated_data:
            validated_data["amount"] = cls.validate_amount(validated_data["amount"])

        if all(key in validated_data for key in ["category", "subcategory"]):
            cls.validate_category_relations(
                validated_data["category"], validated_data["subcategory"]
            )

        return validated_data


class OperationTypeValidator(BaseValidator):
    """Валидатор для типов операций"""

    @classmethod
    def validate_name(cls, name: str, instance=None) -> str:
        """Проверка уникальности имени типа операции"""
        return cls.validate_unique_name(OperationType, name, instance)


class CategoryValidator(BaseValidator):
    """Валидатор для категорий"""

    @classmethod
    def validate_name(cls, name: str, operation_type, instance=None) -> str:
        """Проверка уникальности имени категории в рамках типа операции"""
        name = name.strip()
        qs = Category.objects.filter(name__iexact=name, operation_type=operation_type)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ValidationError(
                "Категория с таким названием уже существует для этого типа операции"
            )
        return name


class SubCategoryValidator(BaseValidator):
    """Валидатор для подкатегорий"""

    @classmethod
    def validate_name(cls, name: str, category, instance=None) -> str:
        """Проверка уникальности имени подкатегории в рамках категории"""
        name = name.strip()
        qs = SubCategory.objects.filter(name__iexact=name, category=category)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ValidationError(
                "Подкатегория с таким названием уже существует для этой категории"
            )
        return name
