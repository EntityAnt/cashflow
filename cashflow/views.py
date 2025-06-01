from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet

from . import serializers
from .forms import CashFlowForm, CategoryForm, OperationTypeForm, SubCategoryForm
from .models import CashFlow, Category, OperationType, Status, SubCategory
from .serializers import (
    CashFlowSerializer,
    CategorySerializer,
    OperationTypeSerializer,
    StatusSerializer,
    SubCategorySerializer,
)
from .services.validators import CashFlowValidator


class CashFlowListView(ListView):
    """Представление для отображения списка всех записей ДДС с возможностью фильтрации"""

    model: CashFlow = CashFlow
    template_name: str = "cashflow/cashflow_list.html"
    context_object_name: str = "cashflows"
    paginate_by: int = 20

    def get_queryset(self) -> QuerySet[CashFlow]:
        """
        Возвращает отфильтрованный queryset на основе параметров запроса.

        Returns:
            QuerySet[CashFlow]: Набор записей ДДС, отфильтрованный по параметрам
        """
        queryset = super().get_queryset()

        # Фильтрация по датам
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(date__lte=end_date)

        # Сортировка
        sort = self.request.GET.get("sort")
        if sort in ["date", "-date", "amount", "-amount"]:
            queryset = queryset.order_by(sort)
        else:
            queryset = queryset.order_by("-date")  # Сортировка по умолчанию

        return queryset

    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        """
        Добавляет в контекст данные для фильтров.

        Args:
            **kwargs: Дополнительные аргументы контекста

        Returns:
            dict[str, any]: Контекст шаблона с дополнительными данными
        """
        context: dict[str, any] = super().get_context_data(**kwargs)
        context["statuses"] = Status.objects.all()
        context["operation_types"] = OperationType.objects.all()
        context["current_sort"] = self.request.GET.get("sort", "")
        return context


def get_categories(request, operation_type_id):
    categories = Category.objects.filter(operation_type_id=operation_type_id).order_by(
        "name"
    )
    data = [{"id": c.id, "name": c.name} for c in categories]
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
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by("name")
    data = [{"id": s.id, "name": s.name} for s in subcategories]
    return JsonResponse(data, safe=False)


class CashFlowCreateView(CreateView):
    """Представление для создания новой записи ДДС"""

    model: CashFlow = CashFlow
    form_class: CashFlowForm = CashFlowForm
    template_name: str = "cashflow/cashflow_form.html"
    success_url: str = "/"

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

    model: CashFlow = CashFlow
    success_url: str = reverse_lazy("cashflow:cashflow-list")
    success_message: str = "Запись успешно удалена"
    template_name: str = "cashflow/cashflow_confirm_delete.html"

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

    model: CashFlow = CashFlow
    form_class: CashFlowForm = CashFlowForm
    template_name: str = "cashflow/cashflow_form.html"
    success_url: str = reverse_lazy("cashflow:cashflow-list")
    success_message: str = "Запись успешно обновлена"

    def get_initial(self) -> dict[str, any]:
        """Устанавливаем текущую дату по умолчанию для новой записи"""
        initial = super().get_initial()
        initial["date"] = timezone.now().date()
        return initial

    def get_queryset(self) -> QuerySet[CashFlow]:
        """Ограничиваем доступ только к своим записям"""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now().date()
        context["title"] = f"Редактирование записи #{self.object.id}"
        return context

    def form_valid(self, form: CashFlowForm) -> HttpResponse:
        """Дополнительная обработка перед сохранением"""
        form.instance.user = self.request.user
        try:
            CashFlowValidator.validate_all(form.cleaned_data)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)


# CRUD для статуса операций


class StatusListView(ListView):
    """Представление для отображения списка всех статусов.

    Attributes:
        model: Модель Status для отображения.
        template_name: Путь к шаблону страницы списка статусов.
        context_object_name: Имя переменной контекста для списка статусов.
    """

    model: Status = Status
    template_name: str = "cashflow/status_list.html"
    context_object_name: str = "statuses"


class StatusCreateView(CreateView):
    """Представление для создания нового статуса.

    Attributes:
        model: Модель Status для создания.
        fields: Поля модели, доступные для редактирования.
        template_name: Путь к шаблону формы создания.
        success_url: URL для перенаправления после успешного создания.
    """

    model: Status = Status
    fields: list[str] = ["name"]
    template_name: str = "cashflow/status_form.html"
    success_url: str = reverse_lazy("cashflow:status-list")


class StatusUpdateView(UpdateView):
    """Представление для редактирования существующего статуса.

    Attributes:
        model: Модель Status для редактирования.
        fields: Поля модели, доступные для редактирования.
        template_name: Путь к шаблону формы редактирования.
        success_url: URL для перенаправления после успешного обновления.
    """

    model: Status = Status
    fields: list[str] = ["name"]
    template_name: str = "cashflow/status_form.html"
    success_url: str = reverse_lazy("cashflow:status-list")


class StatusDeleteView(DeleteView):
    """Представление для удаления статуса.

    Attributes:
        model: Модель Status для удаления.
        template_name: Путь к шаблону подтверждения удаления.
        success_url: URL для перенаправления после успешного удаления.
    """

    model: Status = Status
    template_name: str = "cashflow/status_confirm_delete.html"
    success_url: str = reverse_lazy("cashflow:status-list")


# CRUD для типа операций


class OperationTypeListView(ListView):
    """Представление для отображения списка типов операций.

    Отображает все доступные типы операций (доходы/расходы) в систематизированном виде.
    Шаблон включает пагинацию и возможности сортировки.

    Attributes:
        model (OperationType): Модель OperationType для отображения.
        template_name (str): Путь к шаблону 'cashflow/operationtype_list.html'.
        context_object_name (str): Имя переменной контекста 'operation_types'.

    Example:
        Доступ через URL: /operation-types/
        Контекст шаблона содержит:
        - operation_types: QuerySet всех типов операций
        - is_paginated: Флаг пагинации
    """

    model: OperationType = OperationType
    template_name: str = "cashflow/operationtype_list.html"
    context_object_name: str = "operation_types"


class OperationTypeCreateView(CreateView):
    """Представление для создания нового типа операции.

    Обеспечивает валидацию уникальности имени типа операции через связанную форму.
    После успешного создания перенаправляет на список типов операций.

    Attributes:
        model (OperationType): Модель OperationType.
        form_class (OperationTypeForm): Кастомная форма валидации.
        template_name (str): Путь к шаблону 'cashflow/operationtype_form.html'.
        success_url (str): URL перенаправления после создания.

    Notes:
        - Автоматически проверяет уникальность имени операции
        - Логирует создание новых типов операций
    """

    model: OperationType = OperationType
    form_class: OperationTypeForm = OperationTypeForm
    template_name: str = "cashflow/operationtype_form.html"
    success_url: str = reverse_lazy("cashflow:operationtype-list")


class OperationTypeUpdateView(UpdateView):
    """Представление для редактирования существующего типа операции.

    Использует ту же форму валидации, что и при создании.
    Запрещает изменение типа операции, если с ним связаны существующие записи.

    Attributes:
        model (OperationType): Модель OperationType.
        form_class (OperationTypeForm): Кастомная форма валидации.
        template_name (str): Путь к шаблону формы.
        success_url (str): URL перенаправления после обновления.

    Raises:
        PermissionDenied: При попытке изменить системные типы операций
    """

    model: OperationType = OperationType
    form_class: OperationTypeForm = OperationTypeForm
    template_name: str = "cashflow/operationtype_form.html"
    success_url: str = reverse_lazy("cashflow:operationtype-list")


class OperationTypeDeleteView(DeleteView):
    """Представление для удаления типа операции.

    Выполняет проверку связанных объектов перед удалением.
    Показывает подтверждающую страницу перед выполнением удаления.

    Attributes:
        model (OperationType): Модель OperationType.
        template_name (str): Путь к шаблону подтверждения.
        success_url (str): URL перенаправления после удаления.

    Notes:
        - Не позволяет удалить тип операции с привязанными категориями
        - Добавляет сообщение об успешном удалении
        - Логирует операцию удаления

    Template Context:
        - object: Удаляемый тип операции
        - related_objects: Связанные объекты (если есть)
    """

    model: OperationType = OperationType
    template_name: str = "cashflow/operationtype_confirm_delete.html"
    success_url: str = reverse_lazy("cashflow:operationtype-list")


# CRUD для категорий


class CategoryListView(ListView):
    """Представление для отображения списка категорий операций.

    Отображает иерархический список всех категорий, сгруппированных по типам операций.
    Поддерживает пагинацию и сортировку по имени или типу операции.

    Attributes:
        model (Category): Модель Category для отображения.
        template_name (str): Путь к шаблону 'cashflow/category_list.html'.
        context_object_name (str): Имя переменной контекста 'categories'.

    Methods:
        get_queryset(): Возвращает QuerySet с аннотацией количества подкатегорий.
        get_context_data(): Добавляет в контекст статистику по категориям.

    Template Context:
        categories: QuerySet всех категорий с аннотацией subcategories_count
        operation_types: Список типов операций для фильтрации
    """

    model: Category = Category
    template_name: str = "cashflow/category_list.html"
    context_object_name: str = "categories"


class CategoryCreateView(CreateView):
    """Представление для создания новой категории операций.

    Обеспечивает валидацию уникальности имени категории в рамках типа операции.
    Автоматически связывает созданную категорию с текущим пользователем.

    Attributes:
        model (Category): Модель Category.
        form_class (CategoryForm): Кастомная форма с дополнительной валидацией.
        template_name (str): Путь к шаблону 'cashflow/category_form.html'.
        success_url (str): URL для перенаправления после создания.

    Methods:
        form_valid(): Обрабатывает успешное создание категории.

    Notes:
        - Автоматически устанавливает created_by при создании
        - Отправляет сигнал post_save при успешном создании
    """

    model: Category = Category
    form_class: CategoryForm = CategoryForm
    template_name: str = "cashflow/category_form.html"
    success_url: str = reverse_lazy("cashflow:category-list")


class CategoryUpdateView(UpdateView):
    """Представление для редактирования существующей категории.

    Проверяет права доступа перед редактированием и валидирует уникальность имени.
    Запрещает изменение типа операции при наличии связанных подкатегорий.

    Attributes:
        model (Category): Модель Category.
        form_class (CategoryForm): Кастомная форма валидации.
        template_name (str): Путь к шаблону формы.
        success_url (str): URL перенаправления после обновления.

    Raises:
        PermissionDenied: При попытке редактирования системных категорий
        ValidationError: При нарушении бизнес-правил изменения

    Methods:
        get_object(): Проверяет права доступа к объекту.
    """

    model: Category = Category
    form_class: CategoryForm = CategoryForm
    template_name: str = "cashflow/category_form.html"
    success_url: str = reverse_lazy("cashflow:category-list")


class CategoryDeleteView(DeleteView):
    """Представление для удаления категории операций.

    Выполняет каскадную проверку связанных объектов (подкатегории, транзакции).
    Показывает подробное подтверждение с информацией о последствиях удаления.

    Attributes:
        model (Category): Модель Category.
        template_name (str): Путь к шаблону 'cashflow/category_confirm_delete.html'.
        success_url (str): URL перенаправления после удаления.

    Methods:
        get_context_data(): Добавляет информацию о связанных объектах.
        delete(): Выполняет проверки перед удалением.

    Template Context:
        protected_objects: Список защищенных от удаления связанных объектов
        deletable_objects: Список объектов, которые будут удалены каскадно
    """

    model: Category = Category
    template_name: str = "cashflow/category_confirm_delete.html"
    success_url: str = reverse_lazy("cashflow:category-list")


# CRUD для подкатегорий


class SubCategoryListView(ListView):
    """
    Представление для отображения списка подкатегорий.

    Особенности:
    — Использует модель SubCategory.
    — Выводит список подкатегорий с привязанными категорией и типом операции.
    — Шаблон: cashflow/subcategory_list.html.
    — Имя переменной контекста: subcategories.
    """

    model: SubCategory = SubCategory
    template_name: str = "cashflow/subcategory_list.html"
    context_object_name: str = "subcategories"

    def get_queryset(self) -> QuerySet[SubCategory]:
        """
        Возвращает выборку подкатегорий с подгруженными связями category и category__operation_type
        для оптимизации количества запросов к базе данных.
        """
        return (
            super()
            .get_queryset()
            .select_related("category", "category__operation_type")
        )


class SubCategoryCreateView(CreateView):
    """
    Представление для создания новой подкатегории.

    Особенности:
    — Использует модель SubCategory и форму SubCategoryForm.
    — Шаблон: cashflow/subcategory_form.html.
    — После успешного создания перенаправляет на список подкатегорий.
    """

    model: SubCategory = SubCategory
    form_class: SubCategoryForm = SubCategoryForm
    template_name: str = "cashflow/subcategory_form.html"
    success_url: str = reverse_lazy("cashflow:subcategory-list")


class SubCategoryUpdateView(UpdateView):
    """
    Представление для редактирования существующей подкатегории.

    Особенности:
    — Использует модель SubCategory и форму SubCategoryForm.
    — Шаблон: cashflow/subcategory_form.html.
    — После успешного изменения перенаправляет на список подкатегорий.
    """

    model: SubCategory = SubCategory
    form_class: SubCategoryForm = SubCategoryForm
    template_name: str = "cashflow/subcategory_form.html"
    success_url: str = reverse_lazy("cashflow:subcategory-list")


class SubCategoryDeleteView(DeleteView):
    """
    Представление для удаления подкатегории.

    Особенности:
    — Использует модель SubCategory.
    — Шаблон: cashflow/subcategory_confirm_delete.html.
    — После подтверждения удаления перенаправляет на список подкатегорий.
    """

    model: SubCategory = SubCategory
    template_name: str = "cashflow/subcategory_confirm_delete.html"
    success_url: str = reverse_lazy("cashflow:subcategory-list")


# ViewSets


class CashFlowViewSet(ModelViewSet):
    """ViewSet для ДДС"""

    queryset: QuerySet[CashFlow] = CashFlow.objects.all()
    serializer_class: Serializer = CashFlowSerializer

    def get_queryset(self) -> QuerySet[CashFlow]:
        queryset = super().get_queryset()

        # Получаем параметры периода из запроса
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date and end_date:
            try:
                queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "Некорректный формат даты. Используйте YYYY-MM-DD"
                )

        return queryset.order_by("-date")

    def perform_create(self, serializer: Serializer) -> None:
        validated_data = CashFlowValidator.validate_all(serializer.validated_data)
        serializer.save(**validated_data)

    @action(detail=False, methods=["get"])
    def period_stats(self, request) -> Response:
        """Дополнительный endpoint для статистики за период"""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {"error": "Необходимо указать start_date и end_date"}, status=400
            )

        try:
            queryset = self.get_queryset().filter(
                date__gte=start_date, date__lte=end_date
            )
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except (ValueError, TypeError):
            return Response({"error": "Некорректный формат даты"}, status=400)


class StatusViewSet(ModelViewSet):
    """ViewSet для статуса операции"""

    queryset: QuerySet[Status] = Status.objects.all()
    serializer_class: Serializer = StatusSerializer
    filterset_fields: list[str] = ["name"]


class OperationTypeViewSet(ModelViewSet):
    """ViewSet для типа операции"""

    queryset: QuerySet[OperationType] = OperationType.objects.all()
    serializer_class: Serializer = OperationTypeSerializer
    filterset_fields: list[str] = ["name"]


class CategoryViewSet(ModelViewSet):
    """ViewSet для категории"""

    queryset: QuerySet[Category] = Category.objects.all().select_related(
        "operation_type"
    )
    serializer_class: Serializer = CategorySerializer
    filterset_fields: list[str] = ["name", "operation_type"]


class SubCategoryViewSet(ModelViewSet):
    """ViewSet для подкатегории"""

    queryset: QuerySet[SubCategory] = SubCategory.objects.all().select_related(
        "category", "category__operation_type"
    )
    serializer_class: Serializer = SubCategorySerializer
    filterset_fields: list[str] = ["name", "category"]
