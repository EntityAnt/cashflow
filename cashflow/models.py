from django.db import models
from typing import Optional, List, Dict, Any


class Status(models.Model):
    """Модель для хранения статусов операций (Бизнес, Личное, Налог и др.)"""
    name: str = models.CharField(max_length=100, unique=True, verbose_name="Название статуса")

    def __str__(self) -> str:
        """Строковое представление статуса"""
        return self.name

    class Meta:
        verbose_name: str = "Статус"
        verbose_name_plural: str = "Статусы"


class OperationType(models.Model):
    """Модель для хранения типов операций (Пополнение, Списание)"""
    name: str = models.CharField(max_length=100, unique=True, verbose_name="Тип операции")

    def __str__(self) -> str:
        """Строковое представление типа операции"""
        return self.name

    class Meta:
        verbose_name: str = "Тип операции"
        verbose_name_plural: str = "Типы операций"


class Category(models.Model):
    """
    Модель категорий операций, связанная с типами операций.
    Пример: категория "Маркетинг" для типа "Списание"
    """
    name: str = models.CharField(max_length=100, verbose_name="Название категории")
    operation_type: models.ForeignKey = models.ForeignKey(
        OperationType,
        on_delete=models.CASCADE,
        verbose_name="Тип операции",
        related_name="categories"
    )

    def __str__(self) -> str:
        """Строковое представление категории с указанием типа"""
        return self.name

    class Meta:
        verbose_name: str = "Категория"
        verbose_name_plural: str = "Категории"
        # Обеспечиваем уникальность комбинации имени и типа операции
        unique_together: tuple = ('name', )


class SubCategory(models.Model):
    """Модель подкатегорий, связанных с категориями"""
    name: str = models.CharField(max_length=100, verbose_name="Название подкатегории")
    category: models.ForeignKey = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name="subcategories"
    )

    def __str__(self) -> str:
        """Строковое представление подкатегории с указанием родительской категории"""
        return self.name

    class Meta:
        verbose_name: str = "Подкатегория"
        verbose_name_plural: str = "Подкатегории"
        # Обеспечиваем уникальность комбинации имени и категории
        unique_together: tuple = ('name', )


class CashFlow(models.Model):
    """
    Основная модель для хранения записей о движении денежных средств.
    Содержит все необходимые поля и связи со справочниками.
    """
    date: models.DateField = models.DateField(verbose_name="Дата операции")
    status: models.ForeignKey = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        verbose_name="Статус"
    )
    operation_type: models.ForeignKey = models.ForeignKey(
        OperationType,
        on_delete=models.PROTECT,
        verbose_name="Тип операции"
    )
    category: models.ForeignKey = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория"
    )
    subcategory: models.ForeignKey = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        verbose_name="Подкатегория"
    )
    amount: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Сумма"
    )
    comment: models.TextField = models.TextField(
        blank=True,
        verbose_name="Комментарий"
    )

    def __str__(self) -> str:
        """Строковое представление записи ДДС"""
        return f"{self.date} - {self.amount} ({self.status})"

    class Meta:
        verbose_name: str = "Запись ДДС"
        verbose_name_plural: str = "Записи ДДС"
        ordering: List[str] = ['-date']
