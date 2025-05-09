from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import QuerySet
from typing import Any, Dict, Optional, List, Type

from rest_framework.serializers import Serializer
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
    model: Type[CashFlow] = CashFlow
    form_class: Type[CashFlowForm] = CashFlowForm
    template_name: str = 'cashflow/cashflow_form.html'
    success_url: str = '/'

    def form_valid(self, form: CashFlowForm) -> HttpResponse:
        """
        Обработка валидной формы.

        Args:
            form: Валидная форма CashFlowForm

        Returns:
            HttpResponse: Результат обработки формы
        """
        return super().form_valid(form)


class CashFlowDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Представление для удаления записи о движении денежных средств.
    Требует авторизации пользователя.
    """
    model: Type[CashFlow] = CashFlow
    success_url: str = reverse_lazy('cashflow:cashflow-list')
    success_message: str = "Запись успешно удалена"
    template_name: str = 'cashflow/cashflow_confirm_delete.html'

    def get_queryset(self) -> QuerySet[CashFlow]:
        """
        Возвращает QuerySet с дополнительными проверками прав доступа.

        Returns:
            QuerySet[CashFlow]: Отфильтрованный queryset
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
    model: Type[CashFlow] = CashFlow
    form_class: Type[CashFlowForm] = CashFlowForm
    template_name: str = 'cashflow/cashflow_form.html'
    success_url: str = reverse_lazy('cashflow:cashflow-list')
    success_message: str = "Запись успешно обновлена"

    def get_initial(self) -> Dict[str, Any]:
        """Устанавливаем текущую дату по умолчанию для новой записи"""
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial

    def form_valid(self, form: CashFlowForm) -> HttpResponse:
        """Привязываем запись к текущему пользователю"""
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_queryset(self) -> QuerySet[CashFlow]:
        """Ограничиваем доступ только к своим записям"""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context['current_date'] = timezone.now().date()
        context['title'] = f"Редактирование записи #{self.object.id}"
        return context

    def form_valid(self, form: CashFlowForm) -> HttpResponse:
        """Дополнительная обработка перед сохранением"""
        try:
            CashFlowValidator.validate_all(form.cleaned_data)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)


"""CRUD для статуса операций"""


class StatusListView(ListView):
    model: Type[Status] = Status
    template_name: str = 'cashflow/status_list.html'
    context_object_name: str = 'statuses'


class StatusCreateView(CreateView):
    model: Type[Status] = Status
    fields: list[str] = ['name']
    template_name: str = 'cashflow/status_form.html'
    success_url: str = reverse_lazy('cashflow:status-list')


class StatusUpdateView(UpdateView):
    model: Type[Status] = Status
    fields: list[str] = ['name']
    template_name: str = 'cashflow/status_form.html'
    success_url: str = reverse_lazy('cashflow:status-list')


class StatusDeleteView(DeleteView):
    model: Type[Status] = Status
    template_name: str = 'cashflow/status_confirm_delete.html'
    success_url: str = reverse_lazy('cashflow:status-list')


"""CRUD для типа операций"""


class OperationTypeListView(ListView):
    model: Type[OperationType] = OperationType
    template_name: str = 'cashflow/operationtype_list.html'
    context_object_name: str = 'operation_types'


class OperationTypeCreateView(CreateView):
    model: Type[OperationType] = OperationType
    form_class: Type[OperationTypeForm] = OperationTypeForm
    template_name: str = 'cashflow/operationtype_form.html'
    success_url: str = reverse_lazy('cashflow:operationtype-list')


class OperationTypeUpdateView(UpdateView):
    model: Type[OperationType] = OperationType
    form_class: Type[OperationTypeForm] = OperationTypeForm
    template_name: str = 'cashflow/operationtype_form.html'
    success_url: str = reverse_lazy('cashflow:operationtype-list')


class OperationTypeDeleteView(DeleteView):
    model: Type[OperationType] = OperationType
    template_name: str = 'cashflow/operationtype_confirm_delete.html'
    success_url: str = reverse_lazy('cashflow:operationtype-list')


"""CRUD для категорий"""


class CategoryListView(ListView):
    model: Type[Category] = Category
    template_name: str = 'cashflow/category_list.html'
    context_object_name: str = 'categories'


class CategoryCreateView(CreateView):
    model: Type[Category] = Category
    form_class: Type[CategoryForm] = CategoryForm
    template_name: str = 'cashflow/category_form.html'
    success_url: str = reverse_lazy('cashflow:category-list')


class CategoryUpdateView(UpdateView):
    model: Type[Category] = Category
    form_class: Type[CategoryForm] = CategoryForm
    template_name: str = 'cashflow/category_form.html'
    success_url: str = reverse_lazy('cashflow:category-list')


class CategoryDeleteView(DeleteView):
    model: Type[Category] = Category
    template_name: str = 'cashflow/category_confirm_delete.html'
    success_url: str = reverse_lazy('cashflow:category-list')


"""CRUD для подкатегорий"""


class SubCategoryListView(ListView):
    model: Type[SubCategory] = SubCategory
    template_name: str = 'cashflow/subcategory_list.html'
    context_object_name: str = 'subcategories'

    def get_queryset(self) -> QuerySet[SubCategory]:
        return super().get_queryset().select_related('category', 'category__operation_type')


class SubCategoryCreateView(CreateView):
    model: Type[SubCategory] = SubCategory
    form_class: Type[SubCategoryForm] = SubCategoryForm
    template_name: str = 'cashflow/subcategory_form.html'
    success_url: str = reverse_lazy('cashflow:subcategory-list')


class SubCategoryUpdateView(UpdateView):
    model: Type[SubCategory] = SubCategory
    form_class: Type[SubCategoryForm] = SubCategoryForm
    template_name: str = 'cashflow/subcategory_form.html'
    success_url: str = reverse_lazy('cashflow:subcategory-list')


class SubCategoryDeleteView(DeleteView):
    model: Type[SubCategory] = SubCategory
    template_name: str = 'cashflow/subcategory_confirm_delete.html'
    success_url: str = reverse_lazy('cashflow:subcategory-list')


"""ViewSet для ДДС"""


class CashFlowViewSet(ModelViewSet):
    queryset: QuerySet[CashFlow] = CashFlow.objects.all()
    serializer_class: Type[Serializer] = CashFlowSerializer

    def perform_create(self, serializer: Serializer) -> None:
        validated_data = CashFlowValidator.validate_all(serializer.validated_data)
        serializer.save(**validated_data)


"""ViewSet для статуса операции"""


class StatusViewSet(ModelViewSet):
    queryset: QuerySet[Status] = Status.objects.all()
    serializer_class: Type[Serializer] = StatusSerializer
    filterset_fields: list[str] = ['name']


"""ViewSet для типа операции"""


class OperationTypeViewSet(ModelViewSet):
    queryset: QuerySet[OperationType] = OperationType.objects.all()
    serializer_class: Type[Serializer] = OperationTypeSerializer
    filterset_fields: list[str] = ['name']


"""ViewSet для категории"""


class CategoryViewSet(ModelViewSet):
    queryset: QuerySet[Category] = Category.objects.all().select_related('operation_type')
    serializer_class: Type[Serializer] = CategorySerializer
    filterset_fields: list[str] = ['name', 'operation_type']


"""ViewSet для подкатегории"""


class SubCategoryViewSet(ModelViewSet):
    queryset: QuerySet[SubCategory] = SubCategory.objects.all().select_related('category', 'category__operation_type')
    serializer_class: Type[Serializer] = SubCategorySerializer
    filterset_fields: list[str] = ['name', 'category']
