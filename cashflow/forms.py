from django import forms
from typing import Any, Dict, Optional
from .models import CashFlow, SubCategory


class CashFlowForm(forms.ModelForm):
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

        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Если форма отправлена и содержит данные о категории
        if 'category' in self.data:
            try:
                category_id: int = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass  # Некорректный ID категории
        # Если форма редактирует существующую запись
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')

    def clean(self) -> Dict[str, Any]:
        """
        Дополнительная валидация данных формы.

        Returns:
            Dict[str, Any]: Очищенные данные формы

        Raises:
            forms.ValidationError: Если нарушены бизнес-правила
        """
        cleaned_data: Dict[str, Any] = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')

        # Проверка, что подкатегория принадлежит выбранной категории
        if category and subcategory and subcategory.category != category:
            raise forms.ValidationError(
                "Выбранная подкатегория не принадлежит выбранной категории"
            )

        return cleaned_data