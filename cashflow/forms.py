from typing import Any, Dict

from django import forms
from django.forms import BooleanField, ImageField
from django.utils import timezone

from cashflow.models import CashFlow, Category, OperationType, SubCategory
from cashflow.services import CashFlowValidator


class StyleFormMixin:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field, ImageField):
                field.widget.attrs["class"] = "form-control-file"
            else:
                field.widget.attrs["class"] = "form-control"


class CashFlowForm(StyleFormMixin, forms.ModelForm):
    """
    Форма для создания и редактирования записей ДДС.
    Использует сервисный слой для валидации.
    """

    class Meta:
        model = CashFlow
        fields = "__all__"
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "max": timezone.now().strftime("%Y-%m-%d"),
                },
                format="%Y-%m-%d",
            ),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["subcategory"].queryset = SubCategory.objects.none()

        # Для новой записи устанавливаем текущую дату, если не передано другое значение
        if not self.instance.pk and "date" not in self.data:
            self.initial["date"] = timezone.now().date()

        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = SubCategory.objects.filter(
                    category_id=category_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields["subcategory"].queryset = (
                self.instance.category.subcategories.order_by("name")
            )

    def clean(self) -> Dict[str, Any]:
        """Основная валидация формы"""
        cleaned_data = super().clean()
        return CashFlowValidator.validate_all(cleaned_data)


class OperationTypeForm(forms.ModelForm):
    class Meta:
        model = OperationType
        fields = ["name"]
        labels = {"name": "Название типа*"}

    def clean_name(self) -> str:
        name: str = self.cleaned_data["name"]
        if (
            OperationType.objects.filter(name__iexact=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Тип операции с таким названием уже существует")
        return name


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "operation_type"]
        labels = {"name": "Название категории*", "operation_type": "Тип операции*"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "operation_type": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_name(self) -> str:
        name: str = self.cleaned_data["name"]
        operation_type: OperationType = self.cleaned_data.get("operation_type")
        if (
            operation_type
            and Category.objects.filter(
                name__iexact=name, operation_type=operation_type
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Категория с таким названием уже существует для этого типа операции"
            )
        return name


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ["name", "category"]
        labels = {"name": "Название подкатегории*", "category": "Категория*"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Всегда показываем все категории
        self.fields["category"].queryset = Category.objects.all().select_related(
            "operation_type"
        )

        # Если форма привязана к существующему объекту
        if self.instance and self.instance.pk:
            self.fields["category"].initial = self.instance.category
