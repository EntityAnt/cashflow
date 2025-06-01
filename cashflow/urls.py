from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cashflow.apps import CashflowConfig

from . import views
from .views import (
    CashFlowCreateView,
    CashFlowDeleteView,
    CashFlowListView,
    CashFlowUpdateView,
    CashFlowViewSet,
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryUpdateView,
    CategoryViewSet,
    OperationTypeCreateView,
    OperationTypeDeleteView,
    OperationTypeListView,
    OperationTypeUpdateView,
    OperationTypeViewSet,
    StatusCreateView,
    StatusDeleteView,
    StatusListView,
    StatusUpdateView,
    StatusViewSet,
    SubCategoryCreateView,
    SubCategoryDeleteView,
    SubCategoryListView,
    SubCategoryUpdateView,
    SubCategoryViewSet,
    get_subcategories,
)

app_name = CashflowConfig.name

# Создаем router и регистрируем ViewSet
router = DefaultRouter()
router.register(r"cashflows", CashFlowViewSet, basename="cashflow")
router.register(r"statuses", StatusViewSet, basename="status")
router.register(r"operation-types", OperationTypeViewSet, basename="operationtype")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"subcategories", SubCategoryViewSet, basename="subcategory")

urlpatterns = [
    path("api/", include(router.urls)),
    # Главная страница со списком записей
    path("", CashFlowListView.as_view(), name="cashflow-list"),
    # CRUD операции для записей ДДС
    path("create/", CashFlowCreateView.as_view(), name="cashflow-create"),
    path("<int:pk>/edit/", CashFlowUpdateView.as_view(), name="cashflow-update"),
    path("<int:pk>/delete/", CashFlowDeleteView.as_view(), name="cashflow-delete"),
    # CRUD операции для статуса операций
    path("statuses/", StatusListView.as_view(), name="status-list"),
    path("statuses/create/", StatusCreateView.as_view(), name="status-create"),
    path("statuses/<int:pk>/edit/", StatusUpdateView.as_view(), name="status-update"),
    path("statuses/<int:pk>/delete/", StatusDeleteView.as_view(), name="status-delete"),
    # CRUD операции для типа операций
    path(
        "operation-types/", OperationTypeListView.as_view(), name="operationtype-list"
    ),
    path(
        "operation-types/create/",
        OperationTypeCreateView.as_view(),
        name="operationtype-create",
    ),
    path(
        "operation-types/<int:pk>/edit/",
        OperationTypeUpdateView.as_view(),
        name="operationtype-update",
    ),
    path(
        "operation-types/<int:pk>/delete/",
        OperationTypeDeleteView.as_view(),
        name="operationtype-delete",
    ),
    # CRUD операции для категорий
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/create/", CategoryCreateView.as_view(), name="category-create"),
    path(
        "categories/<int:pk>/edit/",
        CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category-delete",
    ),
    # CRUD операции для подкатегорий
    path("subcategories/", SubCategoryListView.as_view(), name="subcategory-list"),
    path(
        "subcategories/create/",
        SubCategoryCreateView.as_view(),
        name="subcategory-create",
    ),
    path(
        "subcategories/<int:pk>/edit/",
        SubCategoryUpdateView.as_view(),
        name="subcategory-update",
    ),
    path(
        "subcategories/<int:pk>/delete/",
        SubCategoryDeleteView.as_view(),
        name="subcategory-delete",
    ),
    # API endpoint для динамической загрузки
    path(
        "get-categories/<int:operation_type_id>/",
        views.get_categories,
        name="get-categories",
    ),
    path(
        "get-subcategories/<int:category_id>/",
        get_subcategories,
        name="get-subcategories",
    ),
]
