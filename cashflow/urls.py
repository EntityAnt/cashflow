from django.urls import path

from . import views
from .views import (
    CashFlowListView,
    CashFlowCreateView,
    CashFlowUpdateView,
    CashFlowDeleteView,
    get_subcategories, StatusListView, StatusCreateView, StatusUpdateView, StatusDeleteView, OperationTypeListView,
    OperationTypeCreateView, OperationTypeUpdateView, OperationTypeDeleteView, CategoryListView, CategoryCreateView,
    CategoryUpdateView, CategoryDeleteView, SubCategoryListView, SubCategoryCreateView, SubCategoryUpdateView,
    SubCategoryDeleteView,
)
from cashflow.apps import CashflowConfig

app_name = CashflowConfig.name

urlpatterns = [
    # Главная страница со списком записей
    path('', CashFlowListView.as_view(), name='cashflow-list'),

    # CRUD операции для записей ДДС
    path('create/', CashFlowCreateView.as_view(), name='cashflow-create'),
    path('<int:pk>/edit/', CashFlowUpdateView.as_view(), name='cashflow-update'),
    path('<int:pk>/delete/', CashFlowDeleteView.as_view(), name='cashflow-delete'),


    # CRUD операции для статуса операций
    path('statuses/', StatusListView.as_view(), name='status-list'),
    path('statuses/create/', StatusCreateView.as_view(), name='status-create'),
    path('statuses/<int:pk>/edit/', StatusUpdateView.as_view(), name='status-update'),
    path('statuses/<int:pk>/delete/', StatusDeleteView.as_view(), name='status-delete'),

    # CRUD операции для типа операций
    path('operation-types/', OperationTypeListView.as_view(), name='operationtype-list'),
    path('operation-types/create/', OperationTypeCreateView.as_view(), name='operationtype-create'),
    path('operation-types/<int:pk>/edit/', OperationTypeUpdateView.as_view(), name='operationtype-update'),
    path('operation-types/<int:pk>/delete/', OperationTypeDeleteView.as_view(), name='operationtype-delete'),

    # CRUD операции для категорий
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),

    # CRUD операции для подкатегорий
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    path('subcategories/create/', SubCategoryCreateView.as_view(), name='subcategory-create'),
    path('subcategories/<int:pk>/edit/', SubCategoryUpdateView.as_view(), name='subcategory-update'),
    path('subcategories/<int:pk>/delete/', SubCategoryDeleteView.as_view(), name='subcategory-delete'),


    # API endpoint для динамической загрузки
    path('get-categories/<int:operation_type_id>/', views.get_categories, name='get-categories'),
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get-subcategories'),


]
