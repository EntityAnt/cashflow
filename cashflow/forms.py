from django import forms
from typing import Any, Dict, Optional

from django.forms import BooleanField, ImageField, ModelForm

from .models import CashFlow, SubCategory


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fild_name, fild in self.fields.items():
            if isinstance(fild, BooleanField):
                fild.widget.attrs["class"] = "form-check-input"
            elif isinstance(fild, ImageField):
                fild.widget.attrs["class"] = "form-control-file"
            else:
                fild.widget.attrs["class"] = "form-control"


class CashFlowForm(StyleFormMixin, ModelForm):
    """
    Форма для создания и редактирования записей ДДС.
    Обеспечивает динамическую загрузку подкатегорий в зависимости от выбранной категории.
    """

    class Meta:
        model: CashFlow = CashFlow
        fields: str = '__all__'
        widgets: Dict[str, Any] = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Инициализация формы с динамическим queryset для подкатегорий.
        """
        super().__init__(*args, **kwargs)

        # Если форма редактирует существующую запись
        if self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')
        else:
            # Для новой записи - показываем все подкатегории или none, если категория не выбрана
            category_id = self.data.get('category') if 'category' in self.data else None
            if category_id:
                try:
                    self.fields['subcategory'].queryset = SubCategory.objects.filter(
                        category_id=int(category_id)
                    ).order_by('name')
                except (ValueError, TypeError):
                    self.fields['subcategory'].queryset = SubCategory.objects.none()
            else:
                self.fields['subcategory'].queryset = SubCategory.objects.none()

    def clean(self) -> Dict[str, Any]:
        """
        Дополнительная валидация данных формы.
        """
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')

        if category and subcategory:
            if subcategory.category != category:
                raise forms.ValidationError(
                    "Выбранная подкатегория не принадлежит выбранной категории"
                )

        return cleaned_data
