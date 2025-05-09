from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import QuerySet
from typing import Any, Dict, Optional, List

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import CashFlow, SubCategory, Status, OperationType, Category
from .forms import CashFlowForm, OperationTypeForm, CategoryForm, SubCategoryForm
from .serializers import CashFlowSerializer, StatusSerializer, OperationTypeSerializer, CategorySerializer, \
    SubCategorySerializer
from .services import CashFlowValidator


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
        queryset = super().get_queryset()

        # Фильтрация по датам
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__lte=end_date)

        # Сортировка
        sort = self.request.GET.get('sort')
        if sort in ['date', '-date', 'amount', '-amount']:
            queryset = queryset.order_by(sort)
        else:
            queryset = queryset.order_by('-date')  # Сортировка по умолчанию

        return queryset

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
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


def get_categories(request, operation_type_id):
    categories = Category.objects.filter(operation_type_id=operation_type_id).order_by('name')
    data = [{'id': c.id, 'name': c.name} for c in categories]
    return JsonResponse(data, safe=False)


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


class CashFlowUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Представление для редактирования существующей записи ДДС.
    Использует сервисный слой для валидации данных.
    """
    model = CashFlow
    form_class = CashFlowForm
    template_name = 'cashflow/cashflow_form.html'
    success_url = reverse_lazy('cashflow:cashflow-list')
    success_message = "Запись успешно обновлена"

    def get_initial(self):
        """Устанавливаем текущую дату по умолчанию для новой записи"""
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        """Привязываем запись к текущему пользователю"""
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_queryset(self):
        """Ограничиваем доступ только к своим записям (для обычных пользователей)"""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        """Добавляем в поле дата текущую дату и контекст в заголовок страницы"""
        context = super().get_context_data(**kwargs)
        context['current_date'] = timezone.now().date()
        context['title'] = f"Редактирование записи #{self.object.id}"
        return context

    def form_valid(self, form):
        """Дополнительная обработка перед сохранением"""
        # Используем сервисный слой для валидации
        try:
            CashFlowValidator.validate_all(form.cleaned_data)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        return super().form_valid(form)


"""CRUD для статуса операций"""


class StatusListView(ListView):
    model = Status
    template_name = 'cashflow/status_list.html'
    context_object_name = 'statuses'


class StatusCreateView(CreateView):
    model = Status
    fields = ['name']
    template_name = 'cashflow/status_form.html'
    success_url = reverse_lazy('cashflow:status-list')


class StatusUpdateView(UpdateView):
    model = Status
    fields = ['name']
    template_name = 'cashflow/status_form.html'
    success_url = reverse_lazy('cashflow:status-list')


class StatusDeleteView(DeleteView):
    model = Status
    template_name = 'cashflow/status_confirm_delete.html'
    success_url = reverse_lazy('cashflow:status-list')


"""CRUD для типа операций"""


class OperationTypeListView(ListView):
    model = OperationType
    template_name = 'cashflow/operationtype_list.html'
    context_object_name = 'operation_types'


class OperationTypeCreateView(CreateView):
    model = OperationType
    form_class = OperationTypeForm
    template_name = 'cashflow/operationtype_form.html'
    success_url = reverse_lazy('cashflow:operationtype-list')


class OperationTypeUpdateView(UpdateView):
    model = OperationType
    form_class = OperationTypeForm
    template_name = 'cashflow/operationtype_form.html'
    success_url = reverse_lazy('cashflow:operationtype-list')


class OperationTypeDeleteView(DeleteView):
    model = OperationType
    template_name = 'cashflow/operationtype_confirm_delete.html'
    success_url = reverse_lazy('cashflow:operationtype-list')


"""CRUD для категорий"""


# Category Views
class CategoryListView(ListView):
    model = Category
    template_name = 'cashflow/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'cashflow/category_form.html'
    success_url = reverse_lazy('cashflow:category-list')


class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'cashflow/category_form.html'
    success_url = reverse_lazy('cashflow:category-list')


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'cashflow/category_confirm_delete.html'
    success_url = reverse_lazy('cashflow:category-list')


"""CRUD для подкатегорий"""


# SubCategory Views
class SubCategoryListView(ListView):
    model = SubCategory
    template_name = 'cashflow/subcategory_list.html'
    context_object_name = 'subcategories'

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'category__operation_type')


class SubCategoryCreateView(CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'cashflow/subcategory_form.html'
    success_url = reverse_lazy('cashflow:subcategory-list')


class SubCategoryUpdateView(UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'cashflow/subcategory_form.html'
    success_url = reverse_lazy('cashflow:subcategory-list')


class SubCategoryDeleteView(DeleteView):
    model = SubCategory
    template_name = 'cashflow/subcategory_confirm_delete.html'
    success_url = reverse_lazy('cashflow:subcategory-list')


"""ViewSet для ДДС """


class CashFlowViewSet(ModelViewSet):
    queryset = CashFlow.objects.all()
    serializer_class = CashFlowSerializer

    def perform_create(self, serializer):
        # Дополнительная обработка перед сохранением
        validated_data = CashFlowValidator.validate_all(serializer.validated_data)
        serializer.save(**validated_data)


"""ViewSet для статуса операции"""


class StatusViewSet(ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    # permission_classes = [IsAuthenticated]
    filterset_fields = ['name']


"""ViewSet для типа операции"""


class OperationTypeViewSet(ModelViewSet):
    queryset = OperationType.objects.all()
    serializer_class = OperationTypeSerializer
    # permission_classes = [IsAuthenticated]
    filterset_fields = ['name']


"""ViewSet для категории"""


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().select_related('operation_type')
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]
    filterset_fields = ['name', 'operation_type']


"""ViewSet для подкатегории"""


class SubCategoryViewSet(ModelViewSet):
    queryset = SubCategory.objects.all().select_related('category', 'category__operation_type')
    serializer_class = SubCategorySerializer
    # permission_classes = [IsAuthenticated]
    filterset_fields = ['name', 'category']
