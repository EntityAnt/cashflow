from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import QuerySet
from typing import Any, Dict, Optional, List
from .models import CashFlow, SubCategory, Status, OperationType
from .forms import CashFlowForm


class CashFlowListView(ListView):
    """Представление для отображения списка всех записей ДДС с возможностью фильтрации"""
    model: CashFlow = CashFlow
    template_name: str = 'cashflow/cashflow_list.html'
    context_object_name: str = 'cashflows'
    paginate_by: int = 20

    def get_queryset(self) -> QuerySet[CashFlow]:
        """
        Возвращает отфильтрованный queryset на основе параметров запроса.

        Returns:
            QuerySet[CashFlow]: Набор записей ДДС, отфильтрованный по параметрам
        """
        queryset: QuerySet[CashFlow] = super().get_queryset()

        # Фильтрация по дате
        date_from: Optional[str] = self.request.GET.get('date_from')
        date_to: Optional[str] = self.request.GET.get('date_to')
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])

        # Фильтрация по статусу
        status_id: Optional[str] = self.request.GET.get('status')
        if status_id:
            queryset = queryset.filter(status_id=status_id)

        # Другие фильтры (аналогично)
        ...

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Добавляет в контекст данные для фильтров.

        Args:
            **kwargs: Дополнительные аргументы контекста

        Returns:
            Dict[str, Any]: Контекст шаблона с дополнительными данными
        """
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context['statuses'] = Status.objects.all()
        context['operation_types'] = OperationType.objects.all()
        return context


def get_subcategories(request: HttpRequest, category_id: int) -> JsonResponse:
    """
    API endpoint для получения подкатегорий по выбранной категории.

    Args:
        request: HTTP-запрос
        category_id: ID выбранной категории

    Returns:
        JsonResponse: Список подкатегорий в формате JSON
    """
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    data = [{'id': s.id, 'name': s.name} for s in subcategories]
    return JsonResponse(data, safe=False)


class CashFlowCreateView(CreateView):
    """Представление для создания новой записи ДДС"""
    model: CashFlow = CashFlow
    form_class: CashFlowForm = CashFlowForm
    template_name: str = 'cashflow/cashflow_form.html'
    success_url: str = '/'

    def form_valid(self, form: CashFlowForm) -> bool:
        """
        Обработка валидной формы.

        Args:
            form: Валидная форма CashFlowForm

        Returns:
            bool: Результат обработки формы
        """
        # Дополнительная обработка перед сохранением
        return super().form_valid(form)


class CashFlowDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Представление для удаления записи о движении денежных средств.
    Требует авторизации пользователя.
    """
    model = CashFlow
    success_url = reverse_lazy('cashflow:cashflow-list')  # URL для перенаправления после удаления
    success_message = "Запись успешно удалена"
    template_name = 'cashflow/cashflow_confirm_delete.html'  # Шаблон подтверждения удаления

    def get_queryset(self):
        """
        Возвращает QuerySet с дополнительными проверками прав доступа.
        Для суперпользователей - все записи, для остальных - только свои.
        """
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset
